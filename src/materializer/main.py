from src.materializer.postgresql import PostgreSQLMaterializer


def main():
    PostgreSQLMaterializer().start_consuming()


if __name__ == "__main__":
    main()
