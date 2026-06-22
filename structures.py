# parcel_structures.py

class MyQueue:
    """Implementation of a FIFO Queue Data Structure."""
    def __init__(self):
        self.items = []

    def enqueue(self, item):
        self.items.append(item)

    def dequeue(self):
        if not self.is_empty():
            return self.items.pop(0)
        return None

    def is_empty(self):
        return len(self.items) == 0

    def get_all(self):
        return self.items
        
    def sort_by_price(self):
        """Algorithm Implementation: Bubble Sort"""
        n = len(self.items)
        for i in range(n):
            for j in range(0, n - i - 1):
                if self.items[j]['price'] > self.items[j + 1]['price']:
                    # Swap elements
                    self.items[j], self.items[j + 1] = self.items[j + 1], self.items[j]


class StatusMapper:
    """Implementation of a Hash Map Data Structure for O(1) lookups."""
    def __init__(self):
        # Maps a status to its physical location
        self.location_map = {
            "Pending Processing": "Origin Sorting Hub",
            "In Transit": "National Distribution Center",
            "Out for Delivery": "Local Delivery Depot",
            "Delivered": "Final Destination Address",
            "Cancelled": "System"
        }

        # Maps a status to the logical NEXT status
        self.next_status_map = {
            "Pending Processing": "In Transit",
            "In Transit": "Out for Delivery",
            "Out for Delivery": "Delivered",
            "Delivered": "Delivered"
        }

    def get_location(self, status):
        """O(1) Hash Map Retrieval"""
        return self.location_map.get(status, "Unknown Location")
        
    def get_next_status(self, current_status):
        """O(1) Hash Map Retrieval"""
        return self.next_status_map.get(current_status, "Delivered")

class UserStack:
    """Implementation of a Stack Data Structure (LIFO) for User Management."""
    def __init__(self):
        self.stack = []

    def push(self, user):
        """Add a user to the top of the stack."""
        self.stack.append(user)

    def pop(self):
        """Remove and return the top user."""
        if not self.is_empty():
            return self.stack.pop()
        return None

    def is_empty(self):
        return len(self.stack) == 0

    def get_all(self):
        """Returns the items in stack order (newest first)."""
        # Python's list slicing [::-1] naturally reads from top-to-bottom of the stack
        return self.stack[::-1]

    def reverse_order(self):
        """Algorithm Implementation: Reverses the stack order (oldest first)."""
        # This acts as our sorting mechanism when the admin clicks the button
        return self.stack

class BinarySearchUser:
    
    def binary_search_users(users_list, target_name):
        low = 0
        high = len(users_list) - 1
        target = target_name.strip().lower()
    
        while low <= high:
            mid = (low + high) // 2
            mid_name = str(users_list[mid]["first_name"]).lower()
            
            if mid_name == target:
                return users_list[mid]  # Found the user dictionary!
            elif mid_name < target:
                low = mid + 1           # Eliminate left half
            else:
                high = mid - 1          # Eliminate right half
                
        return None  # Not found
class BinarySearchParcel:
    
    def binary_search_parcels(parcel_list, target_item_name):
        
        low = 0
        high = len(parcel_list) - 1
        target = target_item_name.strip().lower()
        results = []
        
        # Phase 1: Use Binary Search to find ANY match containing the keyword
        match_index = -1
        while low <= high:
            mid = (low + high) // 2
            mid_name = str(parcel_list[mid]["item_name"]).lower()
            
            if target in mid_name:
                match_index = mid
                break  # Found an anchor point!
            elif mid_name < target:
                low = mid + 1
            else:
                high = mid - 1
                
        # Phase 2: Linear expansion to gather all neighboring partial matches (since they are sorted together!)
        if match_index != -1:
            results.append(parcel_list[match_index])
            
            # Scan left of the match point
            left = match_index - 1
            while left >= 0 and target in str(parcel_list[left]["item_name"]).lower():
                results.append(parcel_list[left])
                left -= 1
                
            # Scan right of the match point
            right = match_index + 1
            while right < len(parcel_list) and target in str(parcel_list[right]["item_name"]).lower():
                results.append(parcel_list[right])
                right += 1
                
        return results  # Returns a list of all matching items