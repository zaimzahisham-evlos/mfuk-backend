import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("seeded_machines")]

test_payload = {
    "machine_code": "MFUK_M11",
    "machine_name": "Test Machine Update",
    "status": "Maintenance",
    "reason": "Test Machine Update Reason",
}

async def test_superadmin_update_machine(authorized_client_superadmin):
    # get machine
    response = await authorized_client_superadmin.get("/production/machines/MFUK_M00")
    assert response.status_code == 200
    assert response.json()["machine_code"] == "MFUK_M00"
    assert response.json()["machine_name"] == "Machine 00"
    assert response.json()["status"] == "Active"

    # update machine
    response = await authorized_client_superadmin.patch("/production/machines/MFUK_M00", json=test_payload)
    assert response.status_code == 200
    assert response.json()["machine_code"] == "MFUK_M00" # machine code is immutable
    assert response.json()["machine_name"] == test_payload["machine_name"]
    assert response.json()["status"] == "Maintenance"

async def test_admin_update_machine(authorized_client_admin):
    response = await authorized_client_admin.patch("/production/machines/MFUK_M00", json=test_payload)
    assert response.status_code == 200
    assert response.json()["machine_code"] == "MFUK_M00" # machine code is immutable
    assert response.json()["machine_name"] == test_payload["machine_name"]
    assert response.json()["status"] == "Maintenance"

async def test_user_no_permission_update_machine(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.patch("/production/machines/MFUK_M00", json=test_payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access MACHINE_UPDATE"

async def test_update_machine_with_blank_machine_name(authorized_client_admin):
    response = await authorized_client_admin.patch("/production/machines/MFUK_M00", json={"machine_name": ""})
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Value cannot be blank for field machine_name"

async def test_update_machine_with_invalid_status(authorized_client_admin):
    response = await authorized_client_admin.patch("/production/machines/MFUK_M00", json={"status": "Invalid"})
    assert response.status_code == 422
    assert response.json()["detail"] == "Input should be 'Commissioning', 'Active', 'Maintenance', 'Decommissioned' or 'Deleted' for field status"

async def test_update_machine_with_deleted_status(authorized_client_admin):
    response = await authorized_client_admin.patch("/production/machines/MFUK_M00", json={"status": "Deleted"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot update a machine to deleted. Use delete machine endpoint instead."


async def test_update_machine_with_commissioning_status_and_no_reason(authorized_client_admin):
    response = await authorized_client_admin.patch("/production/machines/MFUK_M00", json={"status": "Commissioning"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot update a machine status to commissioning without a reason"

# TODO: test update machine with released recipe versions