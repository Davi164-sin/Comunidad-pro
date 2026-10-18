import os
import shutil

def aplicar_cambios():
    print("Aplicando cambios de 'genesis_os_dev' a 'genesis_os'...")
    try:
        # Copiar contenido
        if os.path.exists("/root/genesis_os_dev"):
            # Eliminar el directorio principal antiguo
            if os.path.exists("/root/genesis_os"):
                shutil.rmtree("/root/genesis_os")
            # Copiar el de desarrollo
            shutil.copytree("/root/genesis_os_dev", "/root/genesis_os")
            print("✅ Cambios aplicados correctamente.")
        else:
            print("❌ No se encontró el directorio de desarrollo.")
    except Exception as e:
        print(f"❌ Error al aplicar cambios: {e}")

if __name__ == "__main__":
    aplicar_cambios()
