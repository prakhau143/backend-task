@app.route('/api/products', methods=['POST'])
def create_product():
    try:
        data = request.json
        
        # Validate required fields
        if not data or 'name' not in data or 'sku' not in data or 'warehouse_id' not in data:
            return {"error": "Missing required fields: name, sku, warehouse_id"}, 400
        
        # Check if SKU already exists (must be unique across platform)
        existing_product = Product.query.filter_by(sku=data['sku']).first()
        if existing_product:
            return {"error": "SKU already exists"}, 409
        
        # Handle optional fields with defaults
        price = float(data.get('price', 0.0)) if data.get('price') is not None else 0.0
        initial_quantity = int(data.get('initial_quantity', 0)) if data.get('initial_quantity') is not None else 0
        
        # Start transaction - create product without warehouse_id (products exist across warehouses)
        product = Product(
            name=data['name'],
            sku=data['sku'],
            price=price
        )
        
        db.session.add(product)
        db.session.flush()  # Get product.id without committing
        
        # Create inventory record for specific warehouse
        inventory = Inventory(
            product_id=product.id,
            warehouse_id=data['warehouse_id'],
            quantity=initial_quantity
        )
        
        db.session.add(inventory)
        db.session.commit()  # Single commit for atomicity
        
        return {"message": "Product created", "product_id": product.id}, 201
        
    except ValueError as e:
        db.session.rollback()
        return {"error": "Invalid data type for price or quantity"}, 400
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal server error"}, 500
