-- Inventory Management System Database Schema
-- Author: System Design
-- Date: 2025-08-01

-- =============================================
-- CORE ENTITIES
-- =============================================

-- Companies table
CREATE TABLE companies (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL, -- Business identifier
    address TEXT,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    tax_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Warehouses table
CREATE TABLE warehouses (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL, -- Warehouse identifier within company
    address TEXT,
    manager_name VARCHAR(255),
    manager_contact VARCHAR(255),
    capacity_cubic_meters DECIMAL(12,2), -- Physical capacity
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, code) -- Warehouse code unique within company
);

-- Suppliers table
CREATE TABLE suppliers (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    payment_terms VARCHAR(100), -- e.g., "Net 30", "COD"
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'blocked')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    id BIGSERIAL PRIMARY KEY,
    sku VARCHAR(100) UNIQUE NOT NULL, -- Stock Keeping Unit
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    brand VARCHAR(100),
    unit_of_measure VARCHAR(20) NOT NULL, -- e.g., 'pieces', 'kg', 'liters'
    weight_kg DECIMAL(10,3),
    dimensions_length_cm DECIMAL(8,2),
    dimensions_width_cm DECIMAL(8,2),
    dimensions_height_cm DECIMAL(8,2),
    is_bundle BOOLEAN DEFAULT FALSE, -- Indicates if this is a bundle product
    cost_price DECIMAL(12,2),
    selling_price DECIMAL(12,2),
    reorder_level INTEGER DEFAULT 0, -- Minimum stock level before reorder
    max_stock_level INTEGER, -- Maximum recommended stock
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- RELATIONSHIP TABLES
-- =============================================

-- Company-Supplier relationships (many-to-many)
CREATE TABLE company_suppliers (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    supplier_id BIGINT NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) DEFAULT 'standard', -- standard, preferred, backup
    contract_start_date DATE,
    contract_end_date DATE,
    credit_limit DECIMAL(12,2),
    payment_terms VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, supplier_id)
);

-- Supplier-Product relationships (what products each supplier provides)
CREATE TABLE supplier_products (
    id BIGSERIAL PRIMARY KEY,
    supplier_id BIGINT NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    supplier_product_code VARCHAR(100), -- Supplier's internal code for the product
    lead_time_days INTEGER, -- How long supplier takes to deliver
    minimum_order_quantity INTEGER DEFAULT 1,
    cost_price DECIMAL(12,2), -- Price from this supplier
    is_preferred_supplier BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(supplier_id, product_id)
);

-- Bundle product components (for products that contain other products)
CREATE TABLE product_bundles (
    id BIGSERIAL PRIMARY KEY,
    bundle_product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    component_product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 1, -- How many of component in bundle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bundle_product_id, component_product_id),
    CHECK (bundle_product_id != component_product_id) -- Prevent self-reference
);

-- =============================================
-- INVENTORY MANAGEMENT
-- =============================================

-- Current inventory levels (snapshot table)
CREATE TABLE inventory (
    id BIGSERIAL PRIMARY KEY,
    warehouse_id BIGINT NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity_available INTEGER NOT NULL DEFAULT 0,
    quantity_reserved INTEGER NOT NULL DEFAULT 0, -- Reserved for orders
    quantity_damaged INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_counted_at TIMESTAMP WITH TIME ZONE, -- Last physical count
    last_counted_by VARCHAR(255), -- Who did the count
    UNIQUE(warehouse_id, product_id),
    CHECK (quantity_available >= 0),
    CHECK (quantity_reserved >= 0),
    CHECK (quantity_damaged >= 0)
);

-- Inventory movement history (audit trail)
CREATE TABLE inventory_movements (
    id BIGSERIAL PRIMARY KEY,
    warehouse_id BIGINT NOT NULL REFERENCES warehouses(id),
    product_id BIGINT NOT NULL REFERENCES products(id),
    movement_type VARCHAR(50) NOT NULL, -- 'in', 'out', 'transfer', 'adjustment', 'damage'
    quantity INTEGER NOT NULL, -- Positive for in, negative for out
    reference_type VARCHAR(50), -- 'purchase', 'sale', 'transfer', 'adjustment', 'return'
    reference_id BIGINT, -- ID of the related document (PO, SO, etc.)
    reason VARCHAR(255),
    batch_number VARCHAR(100),
    expiry_date DATE,
    cost_per_unit DECIMAL(12,2),
    performed_by VARCHAR(255) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Inventory locations within warehouses (optional granular tracking)
CREATE TABLE warehouse_locations (
    id BIGSERIAL PRIMARY KEY,
    warehouse_id BIGINT NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    location_code VARCHAR(50) NOT NULL, -- e.g., 'A1-B2', 'Row-5-Shelf-3'
    location_type VARCHAR(30), -- 'shelf', 'floor', 'cold_storage', 'hazmat'
    description TEXT,
    max_capacity INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(warehouse_id, location_code)
);

-- Product locations (where specific products are stored)
CREATE TABLE inventory_locations (
    id BIGSERIAL PRIMARY KEY,
    inventory_id BIGINT NOT NULL REFERENCES inventory(id) ON DELETE CASCADE,
    location_id BIGINT NOT NULL REFERENCES warehouse_locations(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0,
    CHECK (quantity >= 0)
);

-- =============================================
-- INDEXES FOR PERFORMANCE
-- =============================================

-- Company indexes
CREATE INDEX idx_companies_status ON companies(status);
CREATE INDEX idx_companies_name ON companies(name);

-- Warehouse indexes
CREATE INDEX idx_warehouses_company_id ON warehouses(company_id);
CREATE INDEX idx_warehouses_status ON warehouses(status);

-- Product indexes
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_is_active ON products(is_active);
CREATE INDEX idx_products_is_bundle ON products(is_bundle);

-- Inventory indexes
CREATE INDEX idx_inventory_warehouse_product ON inventory(warehouse_id, product_id);
CREATE INDEX idx_inventory_product_id ON inventory(product_id);
CREATE INDEX idx_inventory_last_updated ON inventory(last_updated);

-- Inventory movements indexes (critical for performance)
CREATE INDEX idx_movements_warehouse_product ON inventory_movements(warehouse_id, product_id);
CREATE INDEX idx_movements_created_at ON inventory_movements(created_at);
CREATE INDEX idx_movements_type ON inventory_movements(movement_type);
CREATE INDEX idx_movements_reference ON inventory_movements(reference_type, reference_id);

-- Supplier relationships indexes
CREATE INDEX idx_company_suppliers_company ON company_suppliers(company_id);
CREATE INDEX idx_supplier_products_supplier ON supplier_products(supplier_id);
CREATE INDEX idx_supplier_products_product ON supplier_products(product_id);

-- Bundle indexes
CREATE INDEX idx_bundles_bundle_product ON product_bundles(bundle_product_id);
CREATE INDEX idx_bundles_component_product ON product_bundles(component_product_id);

-- =============================================
-- TRIGGERS FOR AUTOMATION
-- =============================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_warehouses_updated_at BEFORE UPDATE ON warehouses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_suppliers_updated_at BEFORE UPDATE ON suppliers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_supplier_products_updated_at BEFORE UPDATE ON supplier_products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Update inventory last_updated when quantity changes
CREATE OR REPLACE FUNCTION update_inventory_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_inventory_timestamp BEFORE UPDATE ON inventory FOR EACH ROW EXECUTE FUNCTION update_inventory_timestamp();

-- =============================================
-- SAMPLE VIEWS FOR COMMON QUERIES
-- =============================================

-- Current stock levels across all warehouses
CREATE VIEW v_stock_summary AS
SELECT 
    p.sku,
    p.name as product_name,
    SUM(i.quantity_available) as total_available,
    SUM(i.quantity_reserved) as total_reserved,
    SUM(i.quantity_damaged) as total_damaged,
    COUNT(DISTINCT i.warehouse_id) as warehouse_count,
    MIN(i.last_updated) as oldest_update,
    MAX(i.last_updated) as newest_update
FROM products p
LEFT JOIN inventory i ON p.id = i.product_id
WHERE p.is_active = true
GROUP BY p.id, p.sku, p.name;

-- Low stock alerts
CREATE VIEW v_low_stock_alerts AS
SELECT 
    c.name as company_name,
    w.name as warehouse_name,
    p.sku,
    p.name as product_name,
    i.quantity_available,
    p.reorder_level,
    (p.reorder_level - i.quantity_available) as shortage
FROM inventory i
JOIN warehouses w ON i.warehouse_id = w.id
JOIN companies c ON w.company_id = c.id
JOIN products p ON i.product_id = p.id
WHERE i.quantity_available <= p.reorder_level
AND p.reorder_level > 0
AND p.is_active = true
ORDER BY shortage DESC;
