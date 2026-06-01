# Delivery-Tracking-System-Project
The Parcel Delivery Tracking System is a web-based application that allows users to register, log in, and manage parcel deliveries in a simple and organized way. Users can create parcel delivery requests, view their parcels, and track them in real time using a unique tracking number. The system displays the status of each parcel, such as pending, in transit, or delivered, and optionally shows the full delivery history. Administrators have additional privileges to manage all parcels in the system, update delivery statuses, assign tracking numbers, and oversee registered users. Overall, the system improves transparency, efficiency, and communication in parcel delivery by ensuring both users and admins can monitor parcel progress easily through a centralized platform.

# PARCEL DELIVERY TRACKING SYSTEM BLUEPRINT 

# 1. User Privileges: 
 A normal user is usually a customer sending or receiving parcels. He will be capable of:

-	Account Management:  
a.	Create an account (Register) 
b.	Login/Logout 
c.	View profile 
d.	Update profile info 
e.	Change password

- Parcel Functions: 
a.	Request a parcel delivery 
b.	Add/Edit address for delivery 
c.	View their own parcels 
d.	Track a parcel using a tracking number 
e.	View parcel history

-	Tracking information: (for the current parcel): either pending, collected, in transit, out for delivery or cancelled. 
 
# 2. Admin Privileges: 

-	User Management: 
a.	View all users 
b.	Search users 
c.	Edit user details 
d.	Delete users  
e.	Change delivery address

-	Parcel Management  
a.	View all parcels 
b.	Search any parcels 
c.	Create parcels 
d.	Edit parcel information 
e.	Delete parcels 
f.	Change parcel status
 
-	Reports 
a.	Total parcels 
b.	Delivered parcels 
c.	Pending parcels 
d.	Cancelled parcels 
3.	Database Tables
 	
-	user_credentials: 
a.	id(pk) 
b.	first_name 
c.	last_name 
d.	email 
e.	password 
f.	role 
g.	created_at

-	parcels 
a.	id (pk) 
b.	tracking_number 
c.	item_name 
d.	sender_id(fk from user_credentials(id)) 
e.	recipient_id(fk from user_credentials(id)) 
f.	status 
g.	created_at

-	parcel_trackin_history:  
a.	id 
b.	parcel_id(fk from parcels(id)) 
c.	status 
d.	location 
e.	updated_by 
f.	updated_at 
# 4.	Data Structures: Queues and Hash Table 
In this Parcel Delivery Tracking System, a queue and a hash table are used to efficiently manage parcel operations. The queue follows a First-In-First-Out (FIFO) approach and is used to manage the order in which parcels are processed, ensuring that parcels are handled in the exact sequence they arrive, just like a real delivery warehouse system. On the other hand, the hash table stores parcel information using unique tracking numbers as keys, allowing fast and direct retrieval of parcel details without searching through all records. This makes tracking very efficient since users can instantly access their parcel status using the tracking number. Together, these two data structures improve system performance by ensuring organized processing (queue) and quick data lookup (hash table), making the system both realistic and efficient. 
# 5.	Algorithms: Hash table-based lookup and Bubble sort 
A searching algorithm, specifically hash table-based lookup, is used to quickly retrieve parcel details using a unique tracking number, allowing users to instantly access information such as status, recipient, and delivery progress without scanning through all records.  
In addition, a sorting algorithm, such as bubble sort or insertion sort, is used in the admin dashboard to organize parcels based on attributes like creation date, delivery priority, or status. This helps administrators view and manage parcels in a structured order, improving clarity and decision-making. 
 
 
