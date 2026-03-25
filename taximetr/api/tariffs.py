from fastapi import APIRouter, Depends, HTTPException
from typing import List
from taximetr.model.schemas import TariffCreate, TariffResponse
from taximetr.service.tariffs import TariffService

router = APIRouter(prefix="/tariffs", tags=["tariffs"])


@router.post("/", response_model=TariffResponse)
def create_tariff(tariff: TariffCreate, service: TariffService = Depends()):
    return service.create_tariff(tariff)


@router.get("/", response_model=List[TariffResponse])
def get_tariffs(service: TariffService = Depends()):
    return service.get_all_tariffs()


@router.get("/{tariff_id}", response_model=TariffResponse)
def get_tariff(tariff_id: int, service: TariffService = Depends()):
    tariff = service.get_tariff(tariff_id)
    if not tariff:
        raise HTTPException(status_code=404, detail="Tariff not found")
    return tariff


@router.put("/{tariff_id}", response_model=TariffResponse)
def update_tariff(tariff_id: int, tariff: TariffCreate, service: TariffService = Depends()):
    updated = service.update_tariff(tariff_id, tariff)
    if not updated:
        raise HTTPException(status_code=404, detail="Tariff not found")
    return updated


@router.delete("/{tariff_id}")
def delete_tariff(tariff_id: int, service: TariffService = Depends()):
    if not service.delete_tariff(tariff_id):
        raise HTTPException(status_code=404, detail="Tariff not found")
    return {"tariff_id": tariff_id}