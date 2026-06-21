CREATE  DATABASE IF NOT EXISTS delivery_tracking_system;
USE delivery_tracking_system;
CREATE TABLE user_credentials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    sex ENUM('M', 'F') NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE addresses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    address_label VARCHAR(255) NOT NULL,
    full_address VARCHAR(255) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user_credentials(id) ON DELETE CASCADE
);


CREATE TABLE parcels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(255) NOT NULL,
    weight_kg DECIMAL(5,2), -- Optional: Add details as needed
    dimensions VARCHAR(50), -- Optional: Add details as needed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE delivery_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    parcel_id INT NOT NULL,
    tracking_number VARCHAR(50) NOT NULL UNIQUE,
    delivery_address VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending Processing',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_credentials(id) ON DELETE CASCADE,
    FOREIGN KEY (parcel_id) REFERENCES parcels(id) ON DELETE CASCADE
);


CREATE TABLE tracking_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parcel_id INT NOT NULL,
    tracking_number VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    location VARCHAR(100) NOT NULL,
    remarks TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parcel_id) REFERENCES parcels(id) ON DELETE CASCADE,
    FOREIGN KEY (tracking_number) REFERENCES delivery_requests(tracking_number) ON DELETE CASCADE
);
ALTER TABLE delivery_requests ADD COLUMN price DECIMAL(10,2) AFTER status;
ALTER TABLE parcels ADD COLUMN description TEXT AFTER item_name;