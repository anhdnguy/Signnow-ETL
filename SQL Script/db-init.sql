create table if not exists temp_user (
	id text not null primary key,
	full_name text,
	email text,
	status text,
	last_login bigint,
	access_rights text,
	banned text,
	ip text,
	application text,
	created_at bigint,
	subscription_status text,
	subscription_type text,
	last_login_datetime timestamp,
	created_at_datetime timestamp,
	toexport bool,
	dataloader text
);

create table if not exists "user" (
	id text not null primary key,
	full_name text,
	email text,
	status text,
	last_login bigint,
	access_rights text,
	banned text,
	ip text,
	application text,
	created_at bigint,
	subscription_status text,
	subscription_type text,
	last_login_datetime timestamp,
	created_at_datetime timestamp,
	toexport bool,
	dataloader text
);

create table if not exists document (
	id text not null primary key,
	owner_id text,
	document_name text,
	created timestamp,
	updated timestamp,
	added timestamp,
	original_filename text,
	s3_id text,
	constraint fk_user
		foreign Key(owner_id)
			references "user"(id)
);