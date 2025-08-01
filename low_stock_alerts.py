from flask import Flask, jsonify, request
from sqlalchemy import create_engine, text
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Database configuration - use environment variables in production
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost/inventory_db')
try:
    db_engine = create_engine(DATABASE_URL)
except Exception as e:
    print(f"Database connection failed: {e}")
    db_engine = None

@app.route('/api/companies/<int:company_id>/alerts/low-stock', methods=['GET'])
def low_stock_alerts(company_id):
    """
    Get low-stock alerts for a specific company.
    
    Business Rules:
    - Low stock threshold varies by product type (uses product.reorder_level)
    - Only alert for products with recent sales activity (last 30 days)
    - Handle multiple warehouses per company
    - Include supplier information for reordering
    - Calculate days until stockout based on sales velocity
    """
    try:
        # Validate company_id parameter
        if company_id <= 0:
            return jsonify({"error": "Invalid company ID"}), 400
        
        # Complex query to get low stock alerts with business logic
        query = '''
        WITH recent_sales AS (
            -- Calculate sales velocity (units sold per day) for the last 30 days
            SELECT 
                im.warehouse_id,
                im.product_id,
                SUM(ABS(im.quantity)) as total_sold,
                COUNT(DISTINCT DATE(im.created_at)) as active_days,
                CASE 
                    WHEN COUNT(DISTINCT DATE(im.created_at)) > 0 
                    THEN SUM(ABS(im.quantity))::FLOAT / COUNT(DISTINCT DATE(im.created_at))
                    ELSE 0
                END as daily_sales_rate
            FROM inventory_movements im
            WHERE im.movement_type = 'out' 
              AND im.created_at >= NOW() - INTERVAL '30 days'
              AND im.quantity < 0  -- Outbound movements are negative
            GROUP BY im.warehouse_id, im.product_id
            HAVING SUM(ABS(im.quantity)) > 0  -- Only products with actual sales
        ),
        preferred_suppliers AS (
            -- Get preferred supplier for each product (or any supplier if no preferred)
            SELECT DISTINCT ON (sp.product_id)
                sp.product_id,
                s.id as supplier_id,
                s.name as supplier_name,
                COALESCE(s.email, s.contact_person) as contact_email,
                sp.lead_time_days,
                sp.minimum_order_quantity
            FROM supplier_products sp
            JOIN suppliers s ON s.id = sp.supplier_id
            WHERE sp.is_active = true AND s.status = 'active'
            ORDER BY sp.product_id, sp.is_preferred_supplier DESC, sp.cost_price ASC
        )
        SELECT 
            p.id as product_id,
            p.name as product_name,
            p.sku,
            i.warehouse_id,
            w.name as warehouse_name,
            i.quantity_available as current_stock,
            COALESCE(p.reorder_level, 10) as threshold,  -- Default threshold if not set
            -- Calculate days until stockout based on sales velocity
            CASE 
                WHEN rs.daily_sales_rate > 0 
                THEN CEIL(i.quantity_available::FLOAT / rs.daily_sales_rate)
                ELSE 999  -- No recent sales, set high value
            END as days_until_stockout,
            ps.supplier_id,
            ps.supplier_name,
            ps.contact_email,
            ps.lead_time_days,
            ps.minimum_order_quantity,
            rs.daily_sales_rate,
            rs.total_sold as units_sold_30_days
        FROM inventory i
        JOIN warehouses w ON i.warehouse_id = w.id
        JOIN products p ON i.product_id = p.id
        JOIN recent_sales rs ON rs.warehouse_id = i.warehouse_id AND rs.product_id = i.product_id
        LEFT JOIN preferred_suppliers ps ON ps.product_id = p.id
        WHERE w.company_id = :company_id
          AND i.quantity_available <= COALESCE(p.reorder_level, 10)
          AND p.is_active = true
          AND w.status = 'active'
        ORDER BY 
            CASE 
                WHEN rs.daily_sales_rate > 0 
                THEN CEIL(i.quantity_available::FLOAT / rs.daily_sales_rate)
                ELSE 999
            END ASC,  -- Most urgent first
            i.quantity_available ASC  -- Then by lowest stock
        '''

        with db_engine.connect() as connection:
            result = connection.execute(text(query), {'company_id': company_id})
            alerts = []
            
            for row in result:
                alert = {
                    "product_id": row.product_id,
                    "product_name": row.product_name,
                    "sku": row.sku,
                    "warehouse_id": row.warehouse_id,
                    "warehouse_name": row.warehouse_name,
                    "current_stock": row.current_stock,
                    "threshold": row.threshold,
                    "days_until_stockout": min(row.days_until_stockout, 999),  # Cap at 999
                    "supplier": {
                        "id": row.supplier_id,
                        "name": row.supplier_name or "No Supplier Found",
                        "contact_email": row.contact_email or "No Contact Available"
                    } if row.supplier_id else {
                        "id": None,
                        "name": "No Supplier Found",
                        "contact_email": "No Contact Available"
                    }
                }
                alerts.append(alert)
            
            return jsonify({
                "alerts": alerts,
                "total_alerts": len(alerts)
            }), 200
            
    except ValueError as e:
        return jsonify({"error": "Invalid request parameters"}), 400
    except Exception as e:
        # Log the actual error for debugging (in production, use proper logging)
        print(f"Error in low_stock_alerts: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# Ensure to handle running the app
if __name__ == '__main__':
    app.run(debug=True)

