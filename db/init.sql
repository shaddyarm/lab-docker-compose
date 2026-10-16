CREATE TABLE car_models (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name varchar(100) NOT NULL UNIQUE,
    base_price_rub integer NOT NULL CHECK (base_price_rub > 0)
);

CREATE TABLE valuation_history (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_id integer NOT NULL REFERENCES car_models(id),
    year integer NOT NULL,
    mileage_km integer NOT NULL,
    estimated_price_rub integer NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO car_models (name, base_price_rub) VALUES
    ('Lada Vesta', 1800000),
    ('Kia Rio', 2200000),
    ('Hyundai Solaris', 2300000),
    ('Toyota Corolla', 3100000),
    ('Volkswagen Polo', 2400000);
