import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.auth import create_access_token
from app.models import User
from app.seed_data import seed_database_if_empty

# In-memory SQLite with StaticPool so all connections share the same memory database
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    seed_database_if_empty(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def supplier_token(db_session):
    supplier = db_session.query(User).filter(User.email == "supplier@demo.com").first()
    return create_access_token({"sub": supplier.email, "role": supplier.role, "id": supplier.id})

@pytest.fixture
def buyer_token(db_session):
    buyer = db_session.query(User).filter(User.email == "buyer@demo.com").first()
    return create_access_token({"sub": buyer.email, "role": buyer.role, "id": buyer.id})
