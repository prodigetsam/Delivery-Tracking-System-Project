-- Create the database
CREATE DATABASE IF NOT EXISTS parcel_delivery_system;
USE parcel_delivery_system;
-- 1. Users table
CREATE TABLE user_credentials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    sex VARCHAR(10),
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user'
);

-- 2. Parcels table
CREATE TABLE parcels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    tracking_number VARCHAR(50) UNIQUE NOT NULL,
    delivery_address TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'On Hold',
    FOREIGN KEY (sender_id) REFERENCES user_credentials(id) ON DELETE CASCADE
);

-- 3. Addresses table
CREATE TABLE addresses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    address_label VARCHAR(50) NOT NULL,
    full_address TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user_credentials(id) ON DELETE CASCADE
);

-- 4. Tracking History table
CREATE TABLE tracking_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parcel_id INT NOT NULL,
    status VARCHAR(50),
    location VARCHAR(255),
    remarks TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parcel_id) REFERENCES parcels(id) ON DELETE CASCADE
);