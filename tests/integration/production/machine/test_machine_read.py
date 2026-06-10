import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("seeded_machines")]

async def test_superadmin_get_all_machines(authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/production/machines")
    assert response.status_code == 200
    assert len(response.json()) == 2

async def test_admin_get_all_machines(authorized_client_admin):
    response = await authorized_client_admin.get("/production/machines")
    assert response.status_code == 200
    assert len(response.json()) == 2

async def test_user_no_permission_get_all_machines(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.get("/production/machines")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access MACHINE_VIEW"

async def test_get_machines_with_statuses(authorized_client_admin):
    response = await authorized_client_admin.get("/production/machines?statuses=Active")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["machine_code"] == "MFUK_M00"
    assert response.json()[0]["machine_name"] == "Machine 00"
    assert response.json()[0]["status"] == "Active"
    
async def test_get_machines_with_multiple_statuses(authorized_client_admin):
    response = await authorized_client_admin.get("/production/machines?statuses=Active&statuses=Maintenance")
    assert response.status_code == 200
    assert len(response.json()) == 2

async def test_get_machines_with_deleted(authorized_client_admin):
    response = await authorized_client_admin.get("/production/machines")
    assert response.status_code == 200
    assert len(response.json()) == 2
    
    # delete one machine
    machine = response.json()[0]
    response = await authorized_client_admin.delete(f"/production/machines/{machine['machine_code']}")
    assert response.status_code == 204

    # get machines after deleting one without include_deleted
    response = await authorized_client_admin.get("/production/machines")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # get machines after deleting one with include_deleted
    response = await authorized_client_admin.get("/production/machines?include_deleted=true")
    assert response.status_code == 200
    assert len(response.json()) == 2

    # get machines with deleted status only
    response = await authorized_client_admin.get("/production/machines?include_deleted=true&statuses=Deleted")
    assert response.status_code == 200
    assert len(response.json()) == 1

async def test_get_machine_by_code(authorized_client_admin):
    response = await authorized_client_admin.get("/production/machines/MFUK_M00")
    assert response.status_code == 200
    assert response.json()["machine_code"] == "MFUK_M00"
    assert response.json()["machine_name"] == "Machine 00"
    assert response.json()["status"] == "Active"

async def test_get_machine_by_code_not_found(authorized_client_admin):
    response = await authorized_client_admin.get("/production/machines/MFUK_M01")
    assert response.status_code == 404
    assert response.json()["detail"] == "Machine with code MFUK_M01 not found"

async def test_user_no_permission_get_machine_by_code(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.get("/production/machines/MFUK_M00")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access MACHINE_VIEW"

async def test_get_machine_by_code_deleted(authorized_client_admin):
    response = await authorized_client_admin.get("/production/machines/MFUK_M99")
    assert response.status_code == 200
    assert response.json()["machine_code"] == "MFUK_M99"
    assert response.json()["machine_name"] == "Machine 99"
    assert response.json()["status"] == "Maintenance"
    response = await authorized_client_admin.delete(f"/production/machines/MFUK_M99")
    assert response.status_code == 204
    response = await authorized_client_admin.get("/production/machines/MFUK_M99")
    assert response.status_code == 404
    assert response.json()["detail"] == "Machine with code MFUK_M99 not found"


