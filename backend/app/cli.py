import argparse

from app.db.models import Base
from app.db.session import SessionLocal, engine
from app.modules.auth.service import create_user


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    create_admin = subparsers.add_parser("create-admin")
    create_admin.add_argument("--username", required=True)
    create_admin.add_argument("--password", required=True)
    args = parser.parse_args()

    Base.metadata.create_all(engine)
    if args.command == "create-admin":
        with SessionLocal() as db:
            try:
                create_user(db, args.username, args.password, "admin")
                print("admin created")
            except ValueError as exc:
                if str(exc) == "账号已存在":
                    print("admin already exists")
                else:
                    raise


if __name__ == "__main__":
    main()
