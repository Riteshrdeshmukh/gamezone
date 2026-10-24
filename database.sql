-- Create the database first in pgAdmin (name: gamezone), then run this file in its Query Tool.

DROP TABLE IF EXISTS bookings, messages, games, pricing, admins CASCADE;

CREATE TABLE admins (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

CREATE TABLE pricing (
    id             SERIAL PRIMARY KEY,
    platform       VARCHAR(40) UNIQUE NOT NULL,
    price_per_hour NUMERIC(8,2) NOT NULL CHECK (price_per_hour > 0),
    stations       INT NOT NULL CHECK (stations > 0),
    description    TEXT NOT NULL
);

CREATE TABLE games (
    id          SERIAL PRIMARY KEY,
    title       VARCHAR(100) NOT NULL,
    platform    VARCHAR(40) NOT NULL REFERENCES pricing(platform),
    genre       VARCHAR(40) NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE bookings (
    id            SERIAL PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    phone         VARCHAR(15) NOT NULL,
    email         VARCHAR(120),
    pricing_id    INT NOT NULL REFERENCES pricing(id),
    play_date     DATE NOT NULL,
    start_time    TIME NOT NULL,
    hours         INT NOT NULL CHECK (hours BETWEEN 1 AND 6),
    stations      INT NOT NULL CHECK (stations BETWEEN 1 AND 4),
    total_price   NUMERIC(10,2) NOT NULL,
    status        VARCHAR(20) NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'confirmed', 'cancelled')),
    created_at    TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE messages (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(120) NOT NULL,
    message    TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

INSERT INTO pricing (platform, price_per_hour, stations, description) VALUES
 ('PC',         80,  10, 'High-refresh monitors, mechanical keyboards and low-latency mice.'),
 ('PS5',        150, 6,  'Couch setup with big screens and two controllers per station.'),
 ('Xbox',       150, 4,  'Series X consoles with Game Pass titles ready to play.'),
 ('VR',         300, 2,  'Standing play area with a headset and two controllers.'),
 ('Racing Sim', 250, 2,  'Wheel, pedals and a bucket seat bolted to a rigid rig.');

INSERT INTO games (title, platform, genre, description) VALUES
 ('Valorant',          'PC',         'Shooter',   'Five-versus-five tactical shooter. Bring a full team.'),
 ('Counter-Strike 2',  'PC',         'Shooter',   'Classic bomb-defusal rounds on the latest engine.'),
 ('Dota 2',            'PC',         'MOBA',      'Deep team strategy for long, loud sessions.'),
 ('Tekken 8',          'PS5',        'Fighting',  'Head-to-head fighting. Winner stays on.'),
 ('EA Sports FC',      'PS5',        'Sports',    'Football with friends on the couch setup.'),
 ('Gran Turismo 7',    'PS5',        'Racing',    'Track days with a huge car list.'),
 ('Forza Horizon 5',   'Xbox',       'Racing',    'Open-world driving, split-screen friendly.'),
 ('Halo Infinite',     'Xbox',       'Shooter',   'Arena multiplayer and co-op campaign.'),
 ('Beat Saber',        'VR',         'Rhythm',    'Slice blocks to the beat. Great first VR game.'),
 ('Half-Life: Alyx',   'VR',         'Adventure', 'A full story-driven game built for VR.'),
 ('Assetto Corsa',     'Racing Sim', 'Racing',    'Realistic handling with force-feedback wheels.'),
 ('BeamNG.drive',      'Racing Sim', 'Driving',   'Soft-body physics for crashes and careful driving.');
