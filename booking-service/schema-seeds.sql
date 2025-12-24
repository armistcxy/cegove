-- Sample food items data
-- Insert popcorn items
INSERT INTO food_items (id, name, type, category, price, image_url, available)
VALUES
    ('food-pop-small', 'Small Popcorn', 'POPCORN', 'SNACKS', 50000, 'https://cinema-images.sgp1.cdn.digitaloceanspaces.com/fnb/Screenshot%20from%202025-12-24%2010-46-32.png', true),
    ('food-pop-medium', 'Medium Popcorn', 'POPCORN', 'SNACKS', 72000, 'https://cinema-images.sgp1.cdn.digitaloceanspaces.com/fnb/Screenshot%20from%202025-12-24%2010-46-42.png', true),
    ('food-pop-large', 'Large Popcorn', 'POPCORN', 'SNACKS', 90000, 'https://cinema-images.sgp1.cdn.digitaloceanspaces.com/fnb/Screenshot%20from%202025-12-24%2010-46-48.png', true);

-- Insert drink items
INSERT INTO food_items (id, name, type, category, price, image_url, available)
VALUES
    ('food-drink-soda-small', 'Small Soda', 'DRINK', 'BEVERAGES', 25000, 'https://cinema-images.sgp1.cdn.digitaloceanspaces.com/fnb/Screenshot%20from%202025-12-24%2010-50-28.png', true),
    ('food-drink-soda-large', 'Large Soda', 'DRINK', 'BEVERAGES', 40000, 'https://cinema-images.sgp1.cdn.digitaloceanspaces.com/fnb/Screenshot%20from%202025-12-24%2010-50-34.png', true),
    ('food-drink-juice-small', 'Small Juice', 'DRINK', 'BEVERAGES', 25000, 'https://cinema-images.sgp1.cdn.digitaloceanspaces.com/fnb/Screenshot%20from%202025-12-24%2010-52-32.png', true),
    ('food-drink-juice-large', 'Large Juice', 'DRINK', 'BEVERAGES', 40000, 'https://cinema-images.sgp1.cdn.digitaloceanspaces.com/fnb/Screenshot%20from%202025-12-24%2010-52-38.png', true);

-- Insert combo items
INSERT INTO food_items (id, name, type, category, price, image_url, available)
VALUES
    ('food-combo-basic', 'Basic Combo (Small Popcorn + Small Drink)', 'COMBO', 'BUNDLE', 60000  , 'https://cinema-images.sgp1.cdn.digitaloceanspaces.com/fnb/252ed103-2b95-49cb-a504-4bc34f5902ff.png', true),
    ('food-combo-deluxe', 'Deluxe Combo (Large Popcorn + Large Drink)', 'COMBO', 'BUNDLE', 100000, 'https://cinema-images.sgp1.cdn.digitaloceanspaces.com/fnb/6509b631-2fe6-4c8b-a0c3-ff837b3b6cd2.png', true),
    ('food-combo-family', 'Family Combo (2x Small Popcorn + 2x Small Drink)', 'COMBO', 'BUNDLE', 110000 , 'https://cinema-images.sgp1.cdn.digitaloceanspaces.com/fnb/9690530c-d376-4e7a-87f7-7166c2205b03.png', true);
