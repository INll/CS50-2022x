CREATE TABLE IF NOT EXISTS catalogue(
                    item_id NOT NULL,
                    price TEXT,
                    is_discounted BOOLEAN,
                    discount TEXT,
                    sale_length TEXT,
                    is_limited BOOLEAN,
                    is_available BOOLEAN,
                    discontinue_date TEXT
                    );