from src.system.config_loader import load_config

def main():
    config = load_config("dev")  # 或者不传参数，默认走 APP_ENV
    print("=== Config Loaded ===")
    print("Keys:", list(config.keys()))
    print("Templates dir:", config["paths"]["templates_dir"])
    print("Charts dir:", config["paths"]["charts_dir"])
    print("PDF dir:", config["paths"]["pdf_dir"])
    print("Datas dir:", config["paths"]["docs_datas"])
    print("Email receivers:", config["email"].get("receivers", []))

if __name__ == "__main__":
    main()