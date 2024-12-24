CREATE DATABASE IF NOT EXISTS info;

USE info;

CREATE TABLE IF NOT EXISTS info_user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    middle_name VARCHAR(255),
    last_name VARCHAR(255) NOT NULL,
    contact_number VARCHAR(20),
    email_address VARCHAR(255) UNIQUE NOT NULL,
    address TEXT,
    password VARCHAR(255) NOT NULL,
    role ENUM('User') NOT NULL DEFAULT 'User'
);

CREATE TABLE IF NOT EXISTS info_admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    middle_name VARCHAR(255),
    last_name VARCHAR(255) NOT NULL,
    contact_number VARCHAR(20),
    email_address VARCHAR(255) UNIQUE NOT NULL,
    address TEXT,
    password VARCHAR(255) NOT NULL,
    role ENUM('Admin') NOT NULL DEFAULT 'Admin'
);

CREATE TABLE IF NOT EXISTS register_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    user_role ENUM('Admin', 'Regular User') NOT NULL,
    register_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES info_user(id)
);

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    quantity INT DEFAULT 0,
    category VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2),
    status ENUM('Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled') DEFAULT 'Pending',
    FOREIGN KEY (user_id) REFERENCES info_user(id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT,
    price DECIMAL(10, 2),
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS inventory (
    product_id INT,
    quantity INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (product_id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS receipt (
    ALTER TABLE orders ADD COLUMN product_id INT;
    ALTER TABLE orders ADD CONSTRAINT fk_product FOREIGN KEY (product_id) REFERENCES products(id);
);

INSERT INTO products (product_name, description, price, quantity, category) VALUES
('Laptop', 'High-performance laptop with 16GB RAM', 1200.00, 10, 'Electronics'),
('Smartphone', 'Latest flagship smartphone', 800.00, 20, 'Electronics'),
('T-Shirt', 'Comfortable cotton t-shirt', 20.00, 50, 'Clothing');

INSERT INTO inventory (product_id, quantity) VALUES
(1, 10),
(2, 20),
(3, 50);

INSERT INTO info_user (first_name, middle_name, last_name, contact_number, email_address, address, password, role)
VALUES ('Admin', '', 'User', '1234567890', 'admin@example.com', '123 Admin St', 'admin123', 'Admin');

INSERT INTO info_user (first_name, middle_name, last_name, contact_number, email_address, address, password, role)
VALUES ('Regular', '', 'User', '0987654321', 'user@example.com', '456 User Ave', 'user123', 'Regular User');

INSERT INTO info_user (first_name, middle_name, last_name, contact_number, email_address, address, password, role)
VALUES ('AsiNeo', 'Medina', 'Garcia', '09935366023', 'asgarcia@my.cspc.edu.ph', 'Macabugos, Libon, Albay', '12345678', 'User');

INSERT INTO info_admin (first_name, middle_name, last_name, contact_number, email_address, address, password, role)
VALUES ('AsiNeo', 'Medina', 'Garcia', '09935366023', 'asgarcia@my.cspc.edu.ph', 'Macabugos, Libon, Albay', '12345678', 'Admin');