import os
import sys

path_controller = r"D:\Proyectos\FrontICE\LARAVELBTI\app\Http\Controllers\PersonalController.php"

def update_controller():
    if not os.path.exists(path_controller):
        print(f"Controller path not found: {path_controller}")
        return False
    
    with open(path_controller, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update store validation
    old_store_val = """        $request->validate([
            'nombre' => 'required|string|max:255',
            'usuario' => 'required|string|max:100',
            'password' => 'required|string|min:4',
            'rol' => 'required|string|max:100',
            'permisos_modulos' => 'nullable|array'
        ]);"""
        
    new_store_val = """        $request->validate([
            'nombre' => 'required|string|max:255',
            'usuario' => 'required|string|max:100',
            'password' => 'required|string|min:4',
            'rol' => 'required|string|max:100',
            'permisos_modulos' => 'nullable|array',
            'idBiometrico' => 'nullable|string|max:50',
            'es_servicio_social' => 'nullable',
            'horas_objetivo' => 'nullable|numeric'
        ]);"""

    # 2. Update store payload
    old_store_payload = """        $payload = [
            'nombre' => $request->nombre,
            'usuario' => trim($request->usuario),
            'password' => Hash::make($request->password),
            'rol' => $request->rol,
            'permisos_modulos' => $modulosList,
            'status' => 'ACTIVO'
        ];"""

    new_store_payload = """        $payload = [
            'nombre' => $request->nombre,
            'usuario' => trim($request->usuario),
            'password' => Hash::make($request->password),
            'rol' => $request->rol,
            'permisos_modulos' => $modulosList,
            'status' => 'ACTIVO',
            'idBiometrico' => $request->filled('idBiometrico') ? trim($request->idBiometrico) : null,
            'es_servicio_social' => ($request->boolean('es_servicio_social') || $request->es_servicio_social == '1' || $request->rol === 'Servicio Social') ? 1 : 0,
            'horas_objetivo' => $request->filled('horas_objetivo') ? (int)$request->horas_objetivo : null
        ];"""

    # 3. Update update validation
    old_update_val = """        $request->validate([
            'nombre' => 'required|string|max:255',
            'usuario' => 'required|string|max:100',
            'rol' => 'required|string|max:100',
            'status' => 'required|string|max:20',
            'permisos_modulos' => 'nullable|array',
            'password' => 'nullable|string|min:4'
        ]);"""

    new_update_val = """        $request->validate([
            'nombre' => 'required|string|max:255',
            'usuario' => 'required|string|max:100',
            'rol' => 'required|string|max:100',
            'status' => 'required|string|max:20',
            'permisos_modulos' => 'nullable|array',
            'password' => 'nullable|string|min:4',
            'idBiometrico' => 'nullable|string|max:50',
            'es_servicio_social' => 'nullable',
            'horas_objetivo' => 'nullable|numeric'
        ]);"""

    # 4. Update update payload
    old_update_payload = """        $payload = [
            'nombre' => $request->nombre,
            'usuario' => trim($request->usuario),
            'rol' => $request->rol,
            'permisos_modulos' => $modulosList,
            'status' => $request->status
        ];"""

    new_update_payload = """        $payload = [
            'nombre' => $request->nombre,
            'usuario' => trim($request->usuario),
            'rol' => $request->rol,
            'permisos_modulos' => $modulosList,
            'status' => $request->status,
            'idBiometrico' => $request->filled('idBiometrico') ? trim($request->idBiometrico) : null,
            'es_servicio_social' => ($request->boolean('es_servicio_social') || $request->es_servicio_social == '1' || $request->rol === 'Servicio Social') ? 1 : 0,
            'horas_objetivo' => $request->filled('horas_objetivo') ? (int)$request->horas_objetivo : null
        ];"""

    for o, n, desc in [
        (old_store_val, new_store_val, "store validation"),
        (old_store_payload, new_store_payload, "store payload"),
        (old_update_val, new_update_val, "update validation"),
        (old_update_payload, new_update_payload, "update payload")
    ]:
        if o not in content:
            print(f"Error: Target block '{desc}' not found in controller.")
            return False
        content = content.replace(o, n, 1)

    with open(path_controller, "w", encoding="utf-8") as f:
        f.write(content)

    print("[OK] PersonalController.php updated successfully.")
    return True

if __name__ == "__main__":
    ok = update_controller()
    if not ok:
        sys.exit(1)
