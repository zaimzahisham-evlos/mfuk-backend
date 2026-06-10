import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("seeded_machines")]

async def test_superadmin_delete_machine(authorized_client_superadmin):
    response = await authorized_client_superadmin.delete("/production/machines/MFUK_M00")
    assert response.status_code == 204
    response = await authorized_client_superadmin.get("/production/machines/MFUK_M00")
    assert response.status_code == 404
    assert response.json()["detail"] == "Machine with code MFUK_M00 not found"

async def test_admin_delete_machine(authorized_client_admin):
    response = await authorized_client_admin.delete("/production/machines/MFUK_M00")
    assert response.status_code == 204
    response = await authorized_client_admin.get("/production/machines/MFUK_M00")
    assert response.status_code == 404
    assert response.json()["detail"] == "Machine with code MFUK_M00 not found"

async def test_user_no_permission_delete_machine(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.delete("/production/machines/MFUK_M00")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access MACHINE_DELETE"

async def test_delete_machine_with_nonexistent_machine_code(authorized_client_admin):
    response = await authorized_client_admin.delete("/production/machines/MFUK_M11")
    assert response.status_code == 404
    assert response.json()["detail"] == "Machine with code MFUK_M11 not found"

async def test_delete_machine_with_deleted_status(authorized_client_admin):
    response = await authorized_client_admin.delete("/production/machines/MFUK_M00")
    assert response.status_code == 204
    response = await authorized_client_admin.delete("/production/machines/MFUK_M00")
    assert response.status_code == 404
    assert response.json()["detail"] == "Machine with code MFUK_M00 not found"

@pytest.mark.usefixtures("seeded_recipes")
async def test_delete_machine_with_recipes(authorized_client_admin):
    response = await authorized_client_admin.delete("/production/machines/MFUK_M00")
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot delete a machine with recipes"