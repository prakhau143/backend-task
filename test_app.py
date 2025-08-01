from flask import Flask, jsonify
import json

app = Flask(__name__)

@app.route('/api/companies/<int:company_id>/alerts/low-stock', methods=['GET'])
def low_stock_alerts_mock(company_id):
    """
    Mock version of the low-stock alerts endpoint for testing.
    Returns sample data matching the expected format.
    """
    # Mock data that matches the expected response format
    mock_alerts = [
        {
            "product_id": 123,
            "product_name": "Widget A",
            "sku": "WID-001",
            "warehouse_id": 456,
            "warehouse_name": "Main Warehouse",
            "current_stock": 5,
            "threshold": 20,
            "days_until_stockout": 12,
            "supplier": {
                "id": 789,
                "name": "Supplier Corp",
                "contact_email": "orders@supplier.com"
            }
        },
        {
            "product_id": 124,
            "product_name": "Widget B",
            "sku": "WID-002",
            "warehouse_id": 457,
            "warehouse_name": "Secondary Warehouse",
            "current_stock": 3,
            "threshold": 15,
            "days_until_stockout": 8,
            "supplier": {
                "id": 790,
                "name": "Another Supplier Inc",
                "contact_email": "support@anothersupplier.com"
            }
        }
    ]
    
    # Validate company_id
    if company_id <= 0:
        return jsonify({"error": "Invalid company ID"}), 400
    
    return jsonify({
        "alerts": mock_alerts,
        "total_alerts": len(mock_alerts)
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", "message": "Low-stock alerts API is running"}), 200

if __name__ == '__main__':
    print("Starting mock low-stock alerts API...")
    print("Available endpoints:")
    print("  GET /api/companies/{company_id}/alerts/low-stock")
    print("  GET /health")
    app.run(debug=True, port=5001)
