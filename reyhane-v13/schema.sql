-- Initial RN booking schema. Run in your PostgreSQL SQL editor.


CREATE TABLE IF NOT EXISTS availability (
	date VARCHAR(10) NOT NULL, 
	times TEXT NOT NULL, 
	PRIMARY KEY (date)
)

;


CREATE TABLE IF NOT EXISTS bookings (
	id VARCHAR(36) NOT NULL, 
	request_id VARCHAR(36) NOT NULL, 
	active_slot VARCHAR(20), 
	date VARCHAR(10) NOT NULL, 
	time VARCHAR(5) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	whatsapp VARCHAR(25) NOT NULL, 
	role VARCHAR(30) NOT NULL, 
	content_status VARCHAR(50) NOT NULL, 
	budget VARCHAR(50) NOT NULL, 
	note TEXT NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	meet_link VARCHAR(500) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (request_id), 
	UNIQUE (active_slot)
)

;

CREATE INDEX IF NOT EXISTS ix_bookings_date ON bookings (date);


CREATE TABLE IF NOT EXISTS rate_limits (
	key VARCHAR(100) NOT NULL, 
	count INTEGER NOT NULL, 
	expires INTEGER NOT NULL, 
	PRIMARY KEY (key)
)

;
