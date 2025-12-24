from sqlmodel import SQLModel

convention = {
    'ix': 'ix_%(column_0_label)s',  # Index
    'uq': 'uq_%(table_name)s_%(column_0_name)s',  # Unique constraint
    'ck': 'ck_%(table_name)s_%(constraint_name)s',  # Check constraint
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',  # Foreign key
    'pk': 'pk_%(table_name)s',  # Primary key
}

SQLModel.metadata.naming_convention = convention
