import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("seeded_machines")]

async def test_superadmin_get_all_machines(authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/production/machines")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["page"] == 1
    assert response.json()["limit"] == 20
    assert response.json()["total_pages"] == 1
    assert len(response.json()["items"]) == 2

async def test_admin_get_all_machines(authorized_client_admin):
    response = await authorized_client_admin.get("/production/machines")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["page"] == 1
    assert response.json()["limit"] == 20
    assert response.json()["total_pages"] == 1
    assert len(response.json()["items"]) == 2

async def test_user_no_permission_get_all_machines(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.get("/production/machines")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access MACHINE_VIEW"

async def test_get_machines_with_statuses(authorized_client_admin):
    response = await authorized_client_admin.get("/production/machines?statuses=Active")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["machine_code"] == "MFUK_M00"
    assert response.json()["items"][0]["machine_name"] == "Machine 00"
    assert response.json()["items"][0]["status"] == "Active"
    
async def test_get_machines_with_multiple_statuses(authorized_client_admin):
    response = await authorized_client_admin.get("/production/machines?statuses=Active&statuses=Maintenance")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2

async def test_get_machines_with_deleted(authorized_client_admin):
    response = await authorized_client_admin.get("/production/machines")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2
    
    # delete one machine
    machine = response.json()["items"][0]
    response = await authorized_client_admin.delete(f"/production/machines/{machine['machine_code']}")
    assert response.status_code == 204

    # get machines after deleting one without include_deleted
    response = await authorized_client_admin.get("/production/machines")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1

    # get machines after deleting one with include_deleted
    response = await authorized_client_admin.get("/production/machines?include_deleted=true")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2

    # get machines with deleted status only
    response = await authorized_client_admin.get("/production/machines?include_deleted=true&statuses=Deleted")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1

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

async def test_get_machines_with_pagination(authorized_client_admin):
    response = await authorized_client_admin.get("/production/machines?page=1&limit=1")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["page"] == 1
    assert response.json()["limit"] == 1
    assert response.json()["total_pages"] == 2
    assert len(response.json()["items"]) == 1

async def test_get_machines_search_not_limited_by_page(authorized_client_admin):
    response = await authorized_client_admin.get("/production/machines?search=00&page=1&limit=1")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["machine_code"] == "MFUK_M00"

    response = await authorized_client_admin.get("/production/machines?search=99&page=1&limit=1")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["machine_code"] == "MFUK_M99"