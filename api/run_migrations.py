from db import init_db

if __name__ == '__main__':
    print("Running migrations...")
    init_db()
    print("Migrations complete!") 