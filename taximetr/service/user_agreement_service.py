from fastapi import Depends

from taximetr import tables
from taximetr.database import Session, get_session


class UserAgreementService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def get_user_agreement(self) -> tables.UserAgreement:
        user_agreement = self.session.query(tables.UserAgreement).first()
        return user_agreement

    def create_user_agreement(self, file_url: str) -> tables.UserAgreement:
        user_agreement = tables.UserAgreement(file_url=file_url)
        self.session.add(user_agreement)
        self.session.commit()
        self.session.refresh(user_agreement)
        return user_agreement