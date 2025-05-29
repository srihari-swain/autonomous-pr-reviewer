import uvicorn
from src.configs.config_loader import read_base_config

if __name__ == "__main__":
    config_data = read_base_config()
    
    uvicorn_app_path = config_data.get("app", "src.comms.server.rest_api.api:fast_api_app") # Default if not in config
    host = config_data.get("host", "0.0.0.0")
    port = config_data.get("port", 8000)
    reload = config_data.get("reload", True)
    workers = config_data.get("workers", 1) # Uvicorn's default is 1 if not specified

    uvicorn.run(
        uvicorn_app_path, 
        host=host, 
        port=port, 
        reload=reload,
        workers=workers
    )