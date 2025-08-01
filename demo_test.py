#!/usr/bin/env python3
"""
Low-Stock Alerts API Demo
========================

This script demonstrates the low-stock alerts endpoint implementation
and its business logic without requiring a database connection.
"""

import json
from datetime import datetime

def simulate_low_stock_alerts(company_id):
    """
    Simulate the low-stock alerts business logic.
    
    Business Rules Implemented:
    1. Low stock threshold varies by product type (reorder_level)
    2. Only alert for products with recent sales activity (last 30 days)
    3. Handle multiple warehouses per company
    4. Include supplier information for reordering
    5. Calculate days until stockout based on sales velocity
    """
    
    # Validate input
    if company_id <= 0:
        return {"error": "Invalid company ID"}, 400
    
    # Simulated data that would come from the database query
    mock_data = [
        {
            'product_id': 123,
            'product_name': 'Widget A',
            'sku': 'WID-001',
            'warehouse_id': 456,
            'warehouse_name': 'Main Warehouse',
            'current_stock': 5,
            'threshold': 20,
            'daily_sales_rate': 0.4,  # 0.4 units per day
            'supplier_id': 789,
            'supplier_name': 'Supplier Corp',
            'contact_email': 'orders@supplier.com'
        },
        {
            'product_id': 124,
            'product_name': 'Widget B',
            'sku': 'WID-002',
            'warehouse_id': 457,
            'warehouse_name': 'Secondary Warehouse',
            'current_stock': 3,
            'threshold': 15,
            'daily_sales_rate': 0.25,  # 0.25 units per day
            'supplier_id': 790,
            'supplier_name': 'Another Supplier Inc',
            'contact_email': 'support@anothersupplier.com'
        },
        {
            'product_id': 125,
            'product_name': 'Widget C',
            'sku': 'WID-003',
            'warehouse_id': 456,
            'warehouse_name': 'Main Warehouse',
            'current_stock': 8,
            'threshold': 25,
            'daily_sales_rate': 1.2,  # 1.2 units per day
            'supplier_id': 791,
            'supplier_name': 'Fast Supply Co',
            'contact_email': 'rush@fastsupply.com'
        }
    ]
    
    alerts = []
    for row in mock_data:
        # Calculate days until stockout based on sales velocity
        if row['daily_sales_rate'] > 0:
            days_until_stockout = int(row['current_stock'] / row['daily_sales_rate'])
        else:
            days_until_stockout = 999  # No recent sales
        
        alert = {
            "product_id": row['product_id'],
            "product_name": row['product_name'],
            "sku": row['sku'],
            "warehouse_id": row['warehouse_id'],
            "warehouse_name": row['warehouse_name'],
            "current_stock": row['current_stock'],
            "threshold": row['threshold'],
            "days_until_stockout": min(days_until_stockout, 999),
            "supplier": {
                "id": row['supplier_id'],
                "name": row['supplier_name'],
                "contact_email": row['contact_email']
            }
        }
        alerts.append(alert)
    
    # Sort by urgency (days until stockout, then by current stock level)
    alerts.sort(key=lambda x: (x['days_until_stockout'], x['current_stock']))
    
    return {
        "alerts": alerts,
        "total_alerts": len(alerts)
    }, 200

def demonstrate_sql_query():
    """Show the actual SQL query that would be used in production"""
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
        COALESCE(p.reorder_level, 10) as threshold,
        -- Calculate days until stockout based on sales velocity
        CASE 
            WHEN rs.daily_sales_rate > 0 
            THEN CEIL(i.quantity_available::FLOAT / rs.daily_sales_rate)
            ELSE 999  -- No recent sales, set high value
        END as days_until_stockout,
        ps.supplier_id,
        ps.supplier_name,
        ps.contact_email
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
    return query

def main():
    """Main demo function"""
    print("=" * 60)
    print("LOW-STOCK ALERTS API DEMONSTRATION")
    print("=" * 60)
    
    print("\n1. API Endpoint Structure:")
    print("   GET /api/companies/{company_id}/alerts/low-stock")
    
    print("\n2. Business Rules Implemented:")
    print("   ✓ Low stock threshold varies by product type")
    print("   ✓ Only alert for products with recent sales activity")
    print("   ✓ Handle multiple warehouses per company")
    print("   ✓ Include supplier information for reordering")
    print("   ✓ Calculate days until stockout based on sales velocity")
    
    print("\n3. Testing with Company ID = 1:")
    print("-" * 40)
    
    # Test valid company ID
    response_data, status_code = simulate_low_stock_alerts(1)
    print(f"Status Code: {status_code}")
    print("Response:")
    print(json.dumps(response_data, indent=2))
    
    print("\n4. Testing with Invalid Company ID = -1:")
    print("-" * 40)
    
    # Test invalid company ID
    response_data, status_code = simulate_low_stock_alerts(-1)
    print(f"Status Code: {status_code}")
    print("Response:")
    print(json.dumps(response_data, indent=2))
    
    print("\n5. SQL Query Used in Production:")
    print("-" * 40)
    print(demonstrate_sql_query())
    
    print("\n6. Key Features:")
    print("-" * 40)
    print("• Sales velocity calculation using 30-day moving average")
    print("• Preferred supplier selection with fallback logic")
    print("• Urgency-based sorting (most critical alerts first)")
    print("• Comprehensive error handling and validation")
    print("• Supports multiple warehouses per company")
    print("• Configurable reorder thresholds per product")
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
