import pytest

pytestmark = pytest.mark.asyncio

test_payload = {
    "machine_code": "mfuk_m01",
    "machine_name": "Test Machine"
}

def assert_machine(response, payload, status_code=201):
    assert response.status_code == status_code
    assert response.json()["machine_code"] == payload["machine_code"].upper()
    assert response.json()["machine_name"] == payload["machine_name"]
    assert response.json()["status"] == "Active"
    assert response.json()["created_by_id"] is not None
    assert response.json()["created_at"] is not None
    assert response.json()["updated_at"] is None

async def test_superadmin_create_machine(authorized_client_superadmin):
    response = await authorized_client_superadmin.post("/production/machines", json=test_payload)
    assert_machine(response, test_payload)
    result = await authorized_client_superadmin.get(f"/production/machines/{test_payload['machine_code']}")
    assert_machine(result, test_payload, 200)

async def test_admin_create_machine(authorized_client_admin):
    response = await authorized_client_admin.post("/production/machines", json=test_payload)
    assert_machine(response, test_payload)
    result = await authorized_client_admin.get(f"/production/machines/{test_payload['machine_code']}")
    assert_machine(result, test_payload, 200)

async def test_user_no_role_create_machine(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.post("/production/machines", json=test_payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access MACHINE_CREATE"

async def test_create_machine_with_blank_machine_code(authorized_client_admin):
    payload = test_payload.copy()
    payload["machine_code"] = " "
    response = await authorized_client_admin.post("/production/machines", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field machine_code"

async def test_create_machine_with_blank_machine_name(authorized_client_admin):
    payload = test_payload.copy()
    payload["machine_name"] = " "
    response = await authorized_client_admin.post("/production/machines", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field machine_name"

async def test_create_machine_with_invalid_machine_code_format(authorized_client_admin):
    payload = test_payload.copy()
    machine_codes = ["invalid-code", "mfuk_t01", "mfuk_m01_01", "test_code", "mfuk_m0", "mfuk_m010", "test_m01"]
    for machine_code in machine_codes:
        payload["machine_code"] = machine_code
        response = await authorized_client_admin.post("/production/machines", json=payload)
        assert response.status_code == 422
        assert response.json()["detail"] == "String should match pattern '^MFUK_M[0-9]{2}$' for field machine_code"

async def test_create_machine_with_deleted_status(authorized_client_admin):
    payload = test_payload.copy()
    payload["status"] = "Deleted"
    response = await authorized_client_admin.post("/production/machines", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot create a machine with status Deleted"

async def test_create_machine_with_duplicate_machine_code(authorized_client_admin):
    payload = test_payload.copy()
    response = await authorized_client_admin.post("/production/machines", json=payload)
    assert response.status_code == 201
    response = await authorized_client_admin.post("/production/machines", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Machine with code MFUK_M01 already exists"

