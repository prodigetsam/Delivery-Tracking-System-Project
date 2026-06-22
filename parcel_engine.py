# import collections

# class ParcelSystemEngine:
#     def __init__(self):
#         # ==========================================
#         # REQUIREMENT 1: QUEUES (Pipeline Progression)
#         # ==========================================
#         # A FIFO Queue defining the exact sequence of delivery.
#         # Each stage is a tuple: (Status, Corresponding Location)
#         self.delivery_pipeline = collections.deque([
#             ("Pending Processing", "Origin Sorting Hub"),
#             ("In Transit", "National Distribution Center"),
#             ("Out for Delivery", "Local Delivery Depot"),
#             ("Delivered", "Final Destination Address")
#         ])

#         # ==========================================
#         # REQUIREMENT 2: HASH MAPS (Fast Retrieval)
#         # ==========================================
#         # Dictionary for O(1) tracking number lookups
#         self.parcel_hash_map = {}

#     def load_database_into_memory(self, db_parcels):
#         """Loads raw database rows into our Hash Map for fast operations."""
#         self.parcel_hash_map.clear()
#         for parcel in db_parcels:
#             # The tracking_number is the unique Key
#             self.parcel_hash_map[parcel["tracking_number"]] = parcel

#     def get_parcel_by_tracking(self, tracking_number):
#         """O(1) Hash Map Retrieval"""
#         return self.parcel_hash_map.get(tracking_number, None)

#     def get_next_pipeline_stage(self, current_status, user_address=None):
#         """Queue Progression Logic: Finds the current status and returns the NEXT status and location."""
#         if not current_status:
#             return self.delivery_pipeline[0]

#         clean_status = str(current_status).strip().lower()
#         pipeline_list = list(self.delivery_pipeline)
        
#         for i in range(len(pipeline_list)):
#             if pipeline_list[i][0].strip().lower() == clean_status:
#                 # If the next stage is the last stage (Delivered)
#                 if i + 1 == len(pipeline_list) - 1 or i == len(pipeline_list) - 1:
#                     target_status = pipeline_list[len(pipeline_list) - 1][0]
#                     # Use the actual address if provided, otherwise fall back to placeholder
#                     target_location = user_address if user_address else pipeline_list[len(pipeline_list) - 1][1]
#                     return target_status, target_location
                
#                 # Otherwise, return the normal next stage in the queue
#                 return pipeline_list[i + 1]
        
#         return self.delivery_pipeline[0]
#     # ==========================================
#     # REQUIREMENT 3: SEARCHING ALGORITHM
#     # ==========================================
#     def binary_search_by_name(self, sorted_parcels, target_name):
#         low = 0
#         high = len(sorted_parcels) - 1
#         target = target_name.lower()

#         results = []

#         while low <= high:
#             mid = (low + high) // 2
#             mid_val = sorted_parcels[mid]["item_name"].lower()

#             # Fix: Check if it starts with the target to maintain binary search logic
#             if mid_val.startswith(target):
#                 results.append(sorted_parcels[mid])
#                 break # Found a match
#             elif mid_val < target:
#                 low = mid + 1
#             else:
#                 high = mid - 1

#         return results