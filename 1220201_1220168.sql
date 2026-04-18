DROP DATABASE IF EXISTS 1220201_1220168;
CREATE DATABASE 1220201_1220168;
USE 1220201_1220168;


CREATE TABLE category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    nameCat       VARCHAR(50) NOT NULL,
    descriptionCat VARCHAR(150)
);

-- 2) Supplier
CREATE TABLE supplier (
    supplier_id   INT AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(100) NOT NULL,
    contact_name  VARCHAR(100),
    contact_phone VARCHAR(20),
	email         VARCHAR(100) unique,
    address       VARCHAR(150)
);

-- 3) Branch
CREATE TABLE branch (
    branch_id INT AUTO_INCREMENT PRIMARY KEY,
    nameBranch      VARCHAR(100) NOT NULL,
    city      VARCHAR(50),
    address   VARCHAR(150),
    phone     VARCHAR(20) unique
);


-- 4) Customer
CREATE TABLE customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name  VARCHAR(50)  NOT NULL,
    last_name   VARCHAR(50)  NOT NULL,
    email       VARCHAR(100) UNIQUE,
    phone       VARCHAR(20)
);


-- 5) Staff 
CREATE TABLE staff (
    staff_id    INT AUTO_INCREMENT PRIMARY KEY,
    first_name  VARCHAR(50) NOT NULL,
    last_name   VARCHAR(50) NOT NULL,
    positionStaff   VARCHAR(50),
    salary      DECIMAL(10,2),
    email       VARCHAR(100),
    phone       VARCHAR(20),
    hire_date   DATE,
    branch_id   INT NOT NULL,
	FOREIGN KEY (branch_id) REFERENCES branch(branch_id)

    );

-- 6) Warehouse 
CREATE TABLE warehouse (
    warehouse_id      INT AUTO_INCREMENT PRIMARY KEY,
    name_warehouse    VARCHAR(100),
    location          VARCHAR(100),
    capacity          INT,
    branch_id         INT NOT NULL,
	FOREIGN KEY (branch_id) REFERENCES branch(branch_id)
);


-- 7) Product 
CREATE TABLE product (
    product_id          INT AUTO_INCREMENT PRIMARY KEY,
    product_name        VARCHAR(100) NOT NULL,
    category_id         INT NOT NULL,
    supplier_id         INT NOT NULL,
    sku                 VARCHAR(50) UNIQUE,
    product_description VARCHAR(150),

    purchase_price      DECIMAL(10,2) NOT NULL,  
    unit_price          DECIMAL(10,2) NOT NULL,  

    FOREIGN KEY (category_id) REFERENCES category(category_id),
    FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id)
);

-- 8) Orders
CREATE TABLE orders (
    order_id     INT AUTO_INCREMENT PRIMARY KEY,
    customer_id  INT NOT NULL,
    staff_id     INT NOT NULL,
    branch_id    INT NOT NULL,
    order_date   DATETIME NOT NULL,
	FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
	FOREIGN KEY (staff_id) REFERENCES staff(staff_id),
	FOREIGN KEY (branch_id) REFERENCES branch(branch_id)
);



-- 9) ternary relationship: Handles_Sale (Staff + Order + Customer)
CREATE TABLE Handles_Sale (
	order_id     INT NOT NULL,
	customer_id  INT NOT NULL,
	staff_id     INT NOT NULL,

	PRIMARY KEY (order_id, customer_id, staff_id),

	FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id)

);


-- 10) Inventory
CREATE TABLE inventory (
    inventory_id   INT AUTO_INCREMENT PRIMARY KEY,
    product_id     INT NOT NULL,
    warehouse_id   INT NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    last_updated   DATE,
	FOREIGN KEY (product_id) REFERENCES product(product_id),
	FOREIGN KEY (warehouse_id) REFERENCES warehouse(warehouse_id)
);

-- 11) Purchase 
CREATE TABLE purchase (
    purchase_id     INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id     INT NOT NULL,
    branch_id       INT NOT NULL,
    staff_id        INT NOT NULL,
    purchase_date   DATE NOT NULL,
    total_amount    DECIMAL(10,2) DEFAULT 0,
    invoice_number  VARCHAR(50),

    FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id),
    FOREIGN KEY (branch_id) REFERENCES branch(branch_id),
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id)
);


-- 12)PurchaseDetail
CREATE TABLE purchasedetail (
    purchaseDetail_id INT AUTO_INCREMENT PRIMARY KEY,
    purchase_id       INT NOT NULL,
    warehouse_id      INT NOT NULL,
    product_id        INT NOT NULL,
    quantity          INT NOT NULL DEFAULT 0,
    unit_cost         DECIMAL(10,2),
    
    received_qty      INT,
    arrival_date      DATE,
    statusP            VARCHAR(50),
    
    FOREIGN KEY (purchase_id) REFERENCES purchase(purchase_id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouse(warehouse_id),
    FOREIGN KEY (product_id) REFERENCES product(product_id)
);




-- 13) stockMovment 
CREATE TABLE stockMovment (
	  movement_id    INT PRIMARY KEY AUTO_INCREMENT,
	  movement_date  DATETIME ,
	  movement_type  VARCHAR(40) ,
	  product_id     INT NOT NULL,
	  warehouse_id   INT NOT NULL,
	  staff_id       INT NOT NULL,
	  qty_change     INT,
      
	  FOREIGN KEY (product_id) REFERENCES Product(product_id),
      FOREIGN KEY (warehouse_id) REFERENCES Warehouse(warehouse_id),
      FOREIGN KEY (staff_id) REFERENCES Staff(staff_id)
);
      
-- 14) Order_Item
CREATE TABLE order_item (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id      INT NOT NULL,
    product_id    INT NOT NULL,
    warehouse_id  INT NOT NULL,
    quantity      INT NOT NULL,
    unit_price    DECIMAL(10,2) NOT NULL,

	FOREIGN KEY (order_id) REFERENCES orders(order_id) ON UPDATE CASCADE ON DELETE CASCADE ,
	FOREIGN KEY (product_id) REFERENCES product(product_id) ON UPDATE CASCADE ON DELETE CASCADE,
	FOREIGN KEY (warehouse_id) REFERENCES warehouse(warehouse_id) ON UPDATE CASCADE ON DELETE CASCADE
);

-- 15) Bill
CREATE TABLE bill (
    bill_id         INT AUTO_INCREMENT PRIMARY KEY,
    order_id        INT NOT NULL,
    bill_date       DATE,
    total_amount    DECIMAL(10,2),
    payment_method  VARCHAR(50),
    payment_status  VARCHAR(50),
	FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- ======================================
-- Dummy Data
-- ======================================
-- ======================================
-- 1. Branches (4 branches)

-- ======================================
INSERT INTO branch (nameBranch, city, address, phone) VALUES
('Main Branch', 'Ramallah', 'Al-Manara Street', '022222222'),
('North Branch', 'Nablus', 'Downtown Street', '092222222'),
('South Branch', 'Hebron', 'Old City Road', '022333333'),
('Central Branch', 'Jerusalem', 'Salah El-Din Street', '022444444');

-- ======================================
-- 2. Staff (10 employees)
-- Staff: staff_id, first_name, last_name, positionStaff, salary, email, phone, hire_date, branch_id

-- ======================================
INSERT INTO staff 
(first_name, last_name, positionStaff, salary, email, phone, hire_date, branch_id)
VALUES
-- Main Branch (Branch 1) - 3 employees
('Ahmad', 'Saleh', 'Branch Manager', 4500, 'ahmad@lib.com', '0591111111', '2023-01-10', 1),
('Lina', 'Haddad', 'Cashier', 2500, 'lina@lib.com', '0592222222', '2024-03-01', 1),
('Sara', 'Omar', 'Stock Clerk', 2200, 'sara@lib.com', '0591234567', '2024-05-15', 1),

-- North Branch (Branch 2) - 3 employees
('Yousef', 'Kamal', 'Branch Manager', 4300, 'yousef@lib.com', '0593333333', '2023-02-15', 2),
('Rami', 'Nasser', 'Cashier', 2400, 'rami@lib.com', '0594444444', '2024-06-01', 2),
('Dina', 'Khalil', 'Stock Clerk', 2100, 'dina@lib.com', '0592345678', '2024-08-20', 2),

-- South Branch (Branch 3) - 2 employees
('Mahmoud', 'Ali', 'Branch Manager', 4200, 'mahmoud@lib.com', '0595555555', '2023-03-20', 3),
('Nour', 'Hamdan', 'Cashier', 2300, 'nour@lib.com', '0596666666', '2024-07-10', 3),

-- Central Branch (Branch 4) - 2 employees
('Khaled', 'Zidan', 'Branch Manager', 4400, 'khaled@lib.com', '0597777777', '2023-04-05', 4),
('Maha', 'Shaban', 'Cashier', 2600, 'maha@lib.com', '0598888888', '2024-04-15', 4);

-- ======================================
-- 3. Warehouses (4 warehouses - one per branch)
-- Warehouse: warehouse_id, name_warehouse, location, capacity, branch_id

-- ======================================
INSERT INTO warehouse
(name_warehouse, location, capacity, branch_id)
VALUES
('Main Warehouse', 'Behind Main Branch', 1000, 1),
('North Warehouse', 'Near North Branch', 1000, 2),
('South Warehouse', 'Hebron Industrial Zone', 2000, 3),
('Central Warehouse', 'Jerusalem Storage Area', 1000, 4);

-- ======================================
-- 4. Categories (6 categories)
-- Category: category_id, nameCat, descriptionCat
-- ======================================
INSERT INTO category (nameCat, descriptionCat) VALUES
('Books', 'All kinds of books'),
('Stationery', 'Office and school supplies'),
('Magazines', 'Monthly and weekly magazines'),
('Electronics', 'Calculators and electronic devices'),
('Art Supplies', 'Drawing and painting materials'),
('Gift Items', 'Cards and gift wrapping');

-- ======================================
-- 5. Suppliers (5 suppliers)
-- Supplier: supplier_id, supplier_name, contact_name, contact_phone, email, address
-- ======================================
INSERT INTO supplier
(supplier_name, contact_name, contact_phone, email, address)
VALUES
('Dar Al-Kutub', 'Ali Hassan', '0595555551', 'dar.books@gmail.com', 'Ramallah'),
('Office World', 'Mona Saleh', '0596666661', 'office.world@gmail.com', 'Nablus'),
('Tech Store', 'Basel Ahmad', '0597777771', 'tech.store@gmail.com', 'Hebron'),
('Art Corner', 'Rana Yousef', '0598888881', 'art.corner@gmail.com', 'Jerusalem'),
('Gift House', 'Samer Khalil', '0599999991', 'gift.house@gmail.com', 'Ramallah');

-- ======================================
-- 6. Products (20 products)

-- ======================================
INSERT INTO product
(product_name, category_id, supplier_id, sku, product_description, purchase_price, unit_price)
VALUES
-- Books (Category 1, Supplier 1) - 6 products
('Database Systems Book', 1, 1, 'BK-001', 'University database book', 35, 50),
('Python Programming Book', 1, 1, 'BK-002', 'Python learning book', 30, 45),
('English Grammar Book', 1, 1, 'BK-003', 'Complete English grammar', 25, 38),
('Math Textbook', 1, 1, 'BK-004', 'High school mathematics', 28, 42),
('History of Palestine', 1, 1, 'BK-005', 'Historical overview', 32, 48),
('Children Stories Book', 1, 1, 'BK-006', 'Collection of short stories', 18, 28),

-- Stationery (Category 2, Supplier 2) - 6 products
('Notebook A4', 2, 2, 'ST-001', '200 pages notebook', 3, 5),
('Blue Pen', 2, 2, 'ST-002', 'Blue ink pen', 1, 2),
('Red Pen', 2, 2, 'ST-003', 'Red ink pen', 1, 2),
('Pencil Set', 2, 2, 'ST-004', 'Set of 12 pencils', 5, 8),
('Eraser', 2, 2, 'ST-005', 'White eraser', 0.5, 1),
('Ruler 30cm', 2, 2, 'ST-006', 'Plastic ruler', 2, 3.5),

-- Electronics (Category 4, Supplier 3) - 3 products
('Scientific Calculator', 4, 3, 'EL-001', 'Casio scientific calculator', 45, 65),
('Basic Calculator', 4, 3, 'EL-002', 'Simple calculator', 15, 22),
('USB Flash Drive 32GB', 4, 3, 'EL-003', 'Kingston flash drive', 20, 30),

-- Art Supplies (Category 5, Supplier 4) - 3 products
('Color Pencils Set', 5, 4, 'ART-001', 'Set of 24 colors', 12, 18),
('Watercolor Set', 5, 4, 'ART-002', '12 color watercolor', 18, 28),
('Sketch Book A3', 5, 4, 'ART-003', 'Professional sketch book', 10, 16),

-- Gift Items (Category 6, Supplier 5) - 2 products
('Greeting Card', 6, 5, 'GF-001', 'Birthday greeting card', 2, 4),
('Gift Bag Medium', 6, 5, 'GF-002', 'Decorative gift bag', 3, 5.5);

-- ======================================
-- 7. Inventory (product distribution across warehouses)
-- Inventory: inventory_id, product_id, warehouse_id, stock_quantity, last_updated

-- ======================================
INSERT INTO inventory
(product_id, warehouse_id, stock_quantity, last_updated)
VALUES
-- Main Warehouse (Warehouse 1)
(1, 1, 25, '2025-12-01'), (2, 1, 18, '2025-12-01'), (3, 1, 22, '2025-12-01'),
(7, 1, 150, '2025-12-01'), (8, 1, 300, '2025-12-01'), (9, 1, 250, '2025-12-01'),
(13, 1, 15, '2025-12-01'), (14, 1, 30, '2025-12-01'), (17, 1, 40, '2025-12-01'),

-- North Warehouse (Warehouse 2)
(1, 2, 12, '2025-12-01'), (4, 2, 20, '2025-12-01'), (5, 2, 15, '2025-12-01'),
(7, 2, 80, '2025-12-01'), (10, 2, 100, '2025-12-01'), (11, 2, 200, '2025-12-01'),
(15, 2, 25, '2025-12-01'), (18, 2, 35, '2025-12-01'),

-- South Warehouse (Warehouse 3)
(2, 3, 10, '2025-12-01'), (6, 3, 30, '2025-12-01'), (8, 3, 180, '2025-12-01'),
(12, 3, 45, '2025-12-01'), (13, 3, 10, '2025-12-01'), (16, 3, 20, '2025-12-01'),
(19, 3, 60, '2025-12-01'), (20, 3, 50, '2025-12-01'),

-- Central Warehouse (Warehouse 4)
(3, 4, 16, '2025-12-01'), (4, 4, 14, '2025-12-01'), (9, 4, 220, '2025-12-01'),
(10, 4, 90, '2025-12-01'), (14, 4, 28, '2025-12-01'), (17, 4, 30, '2025-12-01'),
(18, 4, 28, '2025-12-01'), (19, 4, 55, '2025-12-01');

-- ======================================
-- 8. Customers (12 customers)
-- Customer: customer_id, first_name, last_name, email, phone
-- ======================================
INSERT INTO customer (first_name, last_name, email, phone) VALUES
('Haneen', 'Qaisi', 'haneen@gmail.com', '0597777771'),
('Rana', 'Yasin', 'rana@gmail.com', '0598888881'),
('Omar', 'Masri', 'omar@gmail.com', '0599999991'),
('Layla', 'Najjar', 'layla@gmail.com', '0591111121'),
('Fadi', 'Barghouti', 'fadi@gmail.com', '0592222221'),
('Reem', 'Tamimi', 'reem@gmail.com', '0593333331'),
('Tariq', 'Issa', 'tariq@gmail.com', '0594444441'),
('Sawsan', 'Odeh', 'sawsan@gmail.com', '0595555551'),
('Marwan', 'Hijazi', 'marwan@gmail.com', '0596666661'),
('Hiba', 'Awad', 'hiba@gmail.com', '0597777781'),
('Zaid', 'Shahin', 'zaid@gmail.com', '0598888891'),
('Maya', 'Khoury', 'maya@gmail.com', '0599999981');

-- ======================================
-- 9. Orders (15 orders)

-- ======================================
INSERT INTO orders
(customer_id, staff_id, branch_id, order_date)
VALUES
-- December 2025
(1, 2, 1, '2025-12-10 10:30:00'),  -- Staff 2 (Lina) at Branch 1
(2, 5, 2, '2025-12-10 14:20:00'),  -- Staff 5 (Rami) at Branch 2
(3, 8, 3, '2025-12-11 09:15:00'),  -- Staff 8 (Nour) at Branch 3
(4, 10, 4, '2025-12-11 16:40:00'), -- Staff 10 (Maha) at Branch 4
(5, 2, 1, '2025-12-12 11:00:00'),  -- Staff 2 (Lina) at Branch 1
(6, 5, 2, '2025-12-13 13:30:00'),  -- Staff 5 (Rami) at Branch 2
(7, 8, 3, '2025-12-14 10:45:00'),  -- Staff 8 (Nour) at Branch 3
(8, 10, 4, '2025-12-15 15:20:00'), -- Staff 10 (Maha) at Branch 4
(9, 2, 1, '2025-12-16 12:10:00'),  -- Staff 2 (Lina) at Branch 1
(10, 5, 2, '2025-12-17 14:50:00'), -- Staff 5 (Rami) at Branch 2

-- January 2026
(11, 8, 3, '2026-01-05 10:00:00'), -- Staff 8 (Nour) at Branch 3
(12, 10, 4, '2026-01-08 11:30:00'),-- Staff 10 (Maha) at Branch 4
(1, 2, 1, '2026-01-10 13:15:00'),  -- Staff 2 (Lina) at Branch 1
(3, 5, 2, '2026-01-12 15:40:00'),  -- Staff 5 (Rami) at Branch 2
(5, 8, 3, '2026-01-15 09:25:00');  -- Staff 8 (Nour) at Branch 3

-- ======================================
-- 10. Order Items (Order details)
-- Order_Item: order_item_id, order_id, product_id, warehouse_id, quantity, unit_price

-- ======================================
INSERT INTO order_item
(order_id, product_id, warehouse_id, quantity, unit_price)
VALUES
-- Order 1 (Branch 1, Warehouse 1)
(1, 1, 1, 2, 50),
(1, 7, 1, 5, 5),
(1, 8, 1, 10, 2),

-- Order 2 (Branch 2, Warehouse 2)
(2, 4, 2, 1, 42),
(2, 10, 2, 3, 8),

-- Order 3 (Branch 3, Warehouse 3)
(3, 6, 3, 4, 28),
(3, 8, 3, 8, 2),
(3, 19, 3, 2, 4),

-- Order 4 (Branch 4, Warehouse 4)
(4, 3, 4, 2, 38),
(4, 9, 4, 15, 2),
(4, 17, 4, 1, 18),

-- Order 5 (Branch 1, Warehouse 1)
(5, 2, 1, 1, 45),
(5, 13, 1, 1, 65),
(5, 8, 1, 20, 2),

-- Order 6 (Branch 2, Warehouse 2)
(6, 1, 2, 1, 50),
(6, 7, 2, 10, 5),

-- Order 7 (Branch 3, Warehouse 3)
(7, 2, 3, 2, 45),
(7, 16, 3, 1, 28),

-- Order 8 (Branch 4, Warehouse 4)
(8, 14, 4, 2, 22),
(8, 18, 4, 2, 28),
(8, 19, 4, 3, 4),

-- Order 9 (Branch 1, Warehouse 1)
(9, 13, 1, 1, 65),
(9, 17, 1, 2, 18),

-- Order 10 (Branch 2, Warehouse 2)
(10, 5, 2, 1, 48),
(10, 11, 2, 50, 1),

-- Order 11 (Branch 3, Warehouse 3)
(11, 12, 3, 5, 3.5),
(11, 20, 3, 4, 5.5),

-- Order 12 (Branch 4, Warehouse 4)
(12, 4, 4, 3, 42),
(12, 9, 4, 25, 2),

-- Order 13 (Branch 1, Warehouse 1)
(13, 1, 1, 1, 50),
(13, 7, 1, 15, 5),

-- Order 14 (Branch 2, Warehouse 2)
(14, 15, 2, 1, 22),
(14, 18, 2, 1, 28),

-- Order 15 (Branch 3, Warehouse 3)
(15, 6, 3, 3, 28),
(15, 8, 3, 12, 2);

-- ======================================
-- 11. Bills
-- Bill: bill_id, order_id, bill_date, total_amount, payment_method, payment_status

-- ======================================
INSERT INTO bill
(order_id, bill_date, total_amount, payment_method, payment_status)
VALUES
(1, '2025-12-10', 145, 'Cash', 'Paid'),
(2, '2025-12-10', 66, 'Card', 'Paid'),
(3, '2025-12-11', 136, 'Cash', 'Paid'),
(4, '2025-12-11', 124, 'Card', 'Paid'),
(5, '2025-12-12', 150, 'Cash', 'Paid'),
(6, '2025-12-13', 100, 'Card', 'Paid'),
(7, '2025-12-14', 118, 'Cash', 'Paid'),
(8, '2025-12-15', 112, 'Card', 'Paid'),
(9, '2025-12-16', 101, 'Cash', 'Paid'),
(10, '2025-12-17', 98, 'Card', 'Paid'),
(11, '2026-01-05', 39.5, 'Cash', 'Paid'),
(12, '2026-01-08', 176, 'Card', 'Paid'),
(13, '2026-01-10', 125, 'Cash', 'Paid'),
(14, '2026-01-12', 50, 'Card', 'Paid'),
(15, '2026-01-15', 108, 'Cash', 'Paid');

-- ======================================
-- 12. Purchases from Suppliers
-- Purchase: purchase_id, supplier_id, branch_id, staff_id, purchase_date, total_amount, invoice_number

-- ======================================
INSERT INTO purchase
(supplier_id, branch_id, staff_id, purchase_date, total_amount, invoice_number)
VALUES
(1, 1, 1, '2025-11-25', 800, 'INV-1001'),  -- Supplier 1, Branch 1, Staff 1 (Ahmad)
(2, 2, 4, '2025-11-28', 600, 'INV-1002'),  -- Supplier 2, Branch 2, Staff 4 (Yousef)
(3, 3, 7, '2025-12-01', 450, 'INV-1003'),  -- Supplier 3, Branch 3, Staff 7 (Mahmoud)
(4, 4, 9, '2025-12-03', 380, 'INV-1004'),  -- Supplier 4, Branch 4, Staff 9 (Khaled)
(5, 1, 1, '2025-12-05', 200, 'INV-1005'),  -- Supplier 5, Branch 1, Staff 1 (Ahmad)
(1, 2, 4, '2025-12-20', 650, 'INV-1006'),  -- Supplier 1, Branch 2, Staff 4 (Yousef)
(2, 3, 7, '2026-01-02', 550, 'INV-1007'),  -- Supplier 2, Branch 3, Staff 7 (Mahmoud)
(3, 4, 9, '2026-01-10', 400, 'INV-1008');  -- Supplier 3, Branch 4, Staff 9 (Khaled)

-- ======================================
-- 13. Purchase Details
-- PurchaseDetail: purchaseDetail_id, purchase_id, warehouse_id, product_id, quantity, unit_cost, received_qty, arrival_date, statusP

-- ======================================
INSERT INTO purchasedetail
(purchase_id, warehouse_id, product_id, quantity, unit_cost, received_qty, arrival_date, statusP)
VALUES
-- Purchase 1 (Warehouse 1)
(1, 1, 1, 15, 35, 15, '2025-11-26', 'Received'),
(1, 1, 2, 12, 30, 12, '2025-11-26', 'Received'),
(1, 1, 3, 20, 25, 20, '2025-11-26', 'Received'),

-- Purchase 2 (Warehouse 2)
(2, 2, 7, 100, 3, 100, '2025-11-29', 'Received'),
(2, 2, 10, 80, 5, 80, '2025-11-29', 'Received'),
(2, 2, 11, 150, 0.5, 150, '2025-11-29', 'Received'),

-- Purchase 3 (Warehouse 3)
(3, 3, 13, 8, 45, 8, '2025-12-02', 'Received'),
(3, 3, 14, 20, 15, 20, '2025-12-02', 'Received'),

-- Purchase 4 (Warehouse 4)
(4, 4, 17, 25, 12, 25, '2025-12-04', 'Received'),
(4, 4, 18, 20, 18, 20, '2025-12-04', 'Received'),

-- Purchase 5 (Warehouse 1)
(5, 1, 19, 40, 2, 40, '2025-12-06', 'Received'),
(5, 1, 20, 35, 3, 35, '2025-12-06', 'Received'),

-- Purchase 6 (Warehouse 2)
(6, 2, 4, 18, 28, 18, '2025-12-21', 'Received'),
(6, 2, 5, 14, 32, 14, '2025-12-21', 'Received'),

-- Purchase 7 (Warehouse 3)
(7, 3, 12, 40, 2, 40, '2026-01-03', 'Received'),
(7, 3, 16, 18, 10, 18, '2026-01-03', 'Received'),

-- Purchase 8 (Warehouse 4)
(8, 4, 15, 22, 20, 22, '2026-01-11', 'Received');

-- ======================================
-- 14. Stock Movements
-- StockMovement: movement_id, movement_date, movement_type, product_id, warehouse_id, staff_id, qty_change

-- ======================================
INSERT INTO stockMovment
(movement_date, movement_type, product_id, warehouse_id, staff_id, qty_change)
VALUES
-- Purchase movements
('2025-11-26 09:00:00', 'PURCHASE', 1, 1, 1, 15),   -- Staff 1 (Ahmad)
('2025-11-26 09:05:00', 'PURCHASE', 2, 1, 1, 12),
('2025-11-26 09:10:00', 'PURCHASE', 3, 1, 1, 20),
('2025-11-29 10:00:00', 'PURCHASE', 7, 2, 4, 100),  -- Staff 4 (Yousef)
('2025-11-29 10:05:00', 'PURCHASE', 10, 2, 4, 80),
('2025-11-29 10:10:00', 'PURCHASE', 11, 2, 4, 150),
('2025-12-02 11:00:00', 'PURCHASE', 13, 3, 7, 8),   -- Staff 7 (Mahmoud)
('2025-12-02 11:05:00', 'PURCHASE', 14, 3, 7, 20),
('2025-12-04 09:30:00', 'PURCHASE', 17, 4, 9, 25),  -- Staff 9 (Khaled)
('2025-12-04 09:35:00', 'PURCHASE', 18, 4, 9, 20),
('2025-12-06 08:00:00', 'PURCHASE', 19, 1, 1, 40),  -- Staff 1 (Ahmad)
('2025-12-06 08:05:00', 'PURCHASE', 20, 1, 1, 35),

-- Sale movements - December
('2025-12-10 10:35:00', 'SALE', 1, 1, 2, -2),       -- Staff 2 (Lina)
('2025-12-10 10:37:00', 'SALE', 7, 1, 2, -5),
('2025-12-10 10:38:00', 'SALE', 8, 1, 2, -10),
('2025-12-10 14:25:00', 'SALE', 4, 2, 5, -1),       -- Staff 5 (Rami)
('2025-12-10 14:27:00', 'SALE', 10, 2, 5, -3),
('2025-12-11 09:20:00', 'SALE', 6, 3, 8, -4),       -- Staff 8 (Nour)
('2025-12-11 09:22:00', 'SALE', 8, 3, 8, -8),
('2025-12-11 09:23:00', 'SALE', 19, 3, 8, -2),
('2025-12-11 16:45:00', 'SALE', 3, 4, 10, -2),      -- Staff 10 (Maha)
('2025-12-11 16:47:00', 'SALE', 9, 4, 10, -15),
('2025-12-11 16:48:00', 'SALE', 17, 4, 10, -1),
('2025-12-12 11:05:00', 'SALE', 2, 1, 2, -1);       -- Staff 2 (Lina)

