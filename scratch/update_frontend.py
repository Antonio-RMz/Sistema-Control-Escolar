import sys
import os
import re

def update_controller():
    path = r"D:\Proyectos\FrontICE\LARAVELBTI\app\Http\Controllers\DocenteController.php"
    if not os.path.exists(path):
        print(f"Error: Controller path not found: {path}")
        return False
        
    print(f"Updating controller: {path}...")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    target = """        "idBiometrico" => $request->idBiometrico,
        "usuario" => $request->usuario ? trim($request->usuario) : null
    ];"""
    
    replacement = """        "idBiometrico" => $request->idBiometrico,
        "usuario" => $request->usuario ? trim($request->usuario) : null,
        "colorDocente" => $request->colorDocente
    ];"""
    
    if target not in content:
        print("Error: Target block not found in controller.")
        return False
        
    occurrences = content.count(target)
    print(f"Found target block {occurrences} times in controller.")
    new_content = content.replace(target, replacement)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("Controller updated successfully!")
    return True

def update_docentes_view():
    path = r"D:\Proyectos\FrontICE\LARAVELBTI\resources\views\docentes\index.blade.php"
    if not os.path.exists(path):
        print(f"Error: View path not found: {path}")
        return False
        
    print(f"Updating docentes view: {path}...")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # --- Edit 1: Insert color input before Observaciones
    target_1 = """                        <div class="col-12">
                            <label class="form-label">Observaciones</label>
                            <textarea class="form-control form-control-premium" name="observacionesDocente\""""
                            
    replacement_1 = """                        <div class="col-md-6">
                            <label class="form-label">Color Exclusivo (Pastel)</label>
                            <div class="d-flex align-items-center gap-2">
                                <div id="pastelColorPalette" class="d-flex flex-wrap gap-1 align-items-center" style="max-width: 280px;"></div>
                                <div class="position-relative" style="width: 38px; height: 38px;">
                                    <input type="color" class="form-control form-control-color" name="colorDocente" id="formDocenteColor" value="#FFFFFF" style="width: 100%; height: 100%; padding: 0; border-radius: 50%; cursor: pointer; border: 2px solid #cbd5e1; background: none;" title="Color personalizado">
                                </div>
                            </div>
                        </div>

                        <div class="col-12">
                            <label class="form-label">Observaciones</label>
                            <textarea class="form-control form-control-premium" name="observacionesDocente\""""

    if target_1 not in content:
        print("Error: Target 1 (Observaciones) not found in view.")
        return False
    content = content.replace(target_1, replacement_1)
    print("Edit 1 (Form inputs) applied.")

    # --- Edit 2: Insert color badge in row rendering
    target_2 = """            html += `
                <tr>
                    <td>${docente.idDocente}</td>
                    <td>
                        <strong>${docente.nombreDocente}"""
                        
    replacement_2 = """            const colorCircle = `<span class="badge-color-dot" style="display: inline-block; width: 14px; height: 14px; border-radius: 50%; background-color: ${docente.colorDocente || '#FFFFFF'}; border: 1px solid #cbd5e1; margin-right: 8px; vertical-align: middle;" title="Color del Docente"></span>`;

            html += `
                <tr>
                    <td>${docente.idDocente}</td>
                    <td>
                        ${colorCircle}<strong>${docente.nombreDocente}"""

    if target_2 not in content:
        print("Error: Target 2 (Row strong tag) not found in view.")
        return False
    content = content.replace(target_2, replacement_2)
    print("Edit 2 (Table row color circle) applied.")

    # --- Edit 3: Init pastel palette in DOMContentLoaded and inject helper methods
    # Let's search and replace for DOMContentLoaded initialization
    target_3 = """document.addEventListener("DOMContentLoaded", function() {

    cargarDocentes();"""
    
    replacement_3 = """document.addEventListener("DOMContentLoaded", function() {

    cargarDocentes();
    if (typeof initPastelPalette === 'function') {
        initPastelPalette();
    }"""
    
    if target_3 not in content:
        print("Error: Target 3 (DOMContentLoaded init) not found in view.")
        return False
    content = content.replace(target_3, replacement_3)
    print("Edit 3 (Paleta init call) applied.")

    # --- Edit 4: Reset palette and select color in Alta click
    target_4 = """            const form = document.getElementById('formDocente');
            form.reset();
            setFormDisabled(false);"""
            
    replacement_4 = """            const form = document.getElementById('formDocente');
            form.reset();
            setFormDisabled(false);
            if (typeof selectPastelColor === 'function') {
                const randomPastel = pastelColors[Math.floor(Math.random() * pastelColors.length)];
                selectPastelColor(randomPastel);
            }"""
            
    if target_4 not in content:
        print("Error: Target 4 (btnAlta reset) not found in view.")
        return False
    content = content.replace(target_4, replacement_4)
    print("Edit 4 (Alta random color selection) applied.")

    # --- Edit 5: Load color and select in verDocente (using regex to ignore encoding of Contraseña)
    pattern_5 = r"(form\.usuario\.value\s*=\s*d\.usuario\s*\|\|\s*'';\s*form\.password\.value\s*=\s*'';\s*document\.getElementById\('lblFormDocentePassword'\)\.textContent\s*=\s*['\"].+?['\"];\s*form\.password\.placeholder\s*=\s*'No asignada';)"
    
    def repl_5(match):
        return match.group(1) + """\n                    form.colorDocente.value = d.colorDocente || '#FFFFFF';\n                    if (typeof selectPastelColor === 'function') {\n                        selectPastelColor(d.colorDocente || '#FFFFFF');\n                    }"""
        
    content, count = re.subn(pattern_5, repl_5, content)
    if count == 0:
        print("Error: Pattern 5 (verDocente load) not matched.")
        return False
    print(f"Edit 5 (verDocente color load) applied {count} times.")

    # --- Edit 6: Load color and select in editarDocente (using regex to ignore encoding of Nueva Contraseña)
    pattern_6 = r"(form\.usuario\.value\s*=\s*d\.usuario\s*\|\|\s*'';\s*form\.password\.value\s*=\s*'';\s*document\.getElementById\('lblFormDocentePassword'\)\.textContent\s*=\s*['\"].+?['\"];\s*form\.password\.placeholder\s*=\s*'Dejar en blanco para conservar actual';)"
    
    def repl_6(match):
        return match.group(1) + """\n                    form.colorDocente.value = d.colorDocente || '#FFFFFF';\n                    if (typeof selectPastelColor === 'function') {\n                        selectPastelColor(d.colorDocente || '#FFFFFF');\n                    }"""
        
    content, count = re.subn(pattern_6, repl_6, content)
    if count == 0:
        print("Error: Pattern 6 (editarDocente load) not matched.")
        return False
    print(f"Edit 6 (editarDocente color load) applied {count} times.")

    # --- Edit 7: Disable colorDocente in setFormDisabled
    target_7 = """        form.password.disabled = disabled;
        const btnTogglePass = document.getElementById('btnToggleFormDocentePassword');"""
        
    replacement_7 = """        form.password.disabled = disabled;
        if (form.colorDocente) form.colorDocente.disabled = disabled;
        const btnTogglePass = document.getElementById('btnToggleFormDocentePassword');"""
        
    if target_7 not in content:
        print("Error: Target 7 (setFormDisabled) not found in view.")
        return False
    content = content.replace(target_7, replacement_7)
    print("Edit 7 (Disable color select in view mode) applied.")

    # --- Edit 8: Include colorDocente in submit payload
    target_8 = """            usuario: this.usuario.value,
            password: this.password.value
        };"""
        
    replacement_8 = """            usuario: this.usuario.value,
            password: this.password.value,
            colorDocente: this.colorDocente.value
        };"""
        
    if target_8 not in content:
        print("Error: Target 8 (Submit data payload) not found in view.")
        return False
    content = content.replace(target_8, replacement_8)
    print("Edit 8 (Submit payload data) applied.")

    # --- Edit 9: Inject pastel palette helper functions at the bottom of the script
    # We will search for window.abrirModalCredenciales and inject above it
    target_9 = """    // ==========================================
    // GESTI"""
    
    # We do a replacement by matching "// ==========================================" followed by "GESTI"
    pattern_9 = r"(// ==========================================\s*// GESTI.+?N DE CREDENCIALES)"
    
    palette_js = """
    // ==========================================
    // GESTIÓN DE COLORES PASTEL DE DOCENTES
    // ==========================================
    const pastelColors = [
        '#FFD6D6', '#D6E4FF', '#D4EDDA', '#F3E5F5', '#FFF3CD', 
        '#FFE8D6', '#D1ECF1', '#FAD2E1', '#E8F5E9', '#ECEFF1', 
        '#C5D3E8', '#E8DFF5'
    ];

    window.initPastelPalette = function() {
        const palette = document.getElementById('pastelColorPalette');
        if (!palette) return;
        palette.innerHTML = '';
        
        pastelColors.forEach(color => {
            const bubble = document.createElement('div');
            bubble.className = 'color-bubble';
            bubble.style.width = '24px';
            bubble.style.height = '24px';
            bubble.style.borderRadius = '50%';
            bubble.style.backgroundColor = color;
            bubble.style.cursor = 'pointer';
            bubble.style.border = '1px solid #cbd5e1';
            bubble.style.transition = 'all 0.2s';
            bubble.title = color;
            
            bubble.addEventListener('click', () => {
                const form = document.getElementById('formDocente');
                if (form.nombreDocente.disabled) return; // View mode, disabled
                selectPastelColor(color);
            });
            
            palette.appendChild(bubble);
        });
    }

    window.selectPastelColor = function(color) {
        const input = document.getElementById('formDocenteColor');
        if (input) {
            input.value = color;
        }
        
        const bubbles = document.querySelectorAll('#pastelColorPalette .color-bubble');
        bubbles.forEach(b => {
            if (b.title.toUpperCase() === color.toUpperCase()) {
                b.style.border = '2.5px solid #26687b';
                b.style.transform = 'scale(1.15)';
            } else {
                b.style.border = '1px solid #cbd5e1';
                b.style.transform = 'scale(1)';
            }
        });
    }

    document.getElementById('formDocenteColor')?.addEventListener('input', function() {
        const color = this.value;
        const bubbles = document.querySelectorAll('#pastelColorPalette .color-bubble');
        bubbles.forEach(b => {
            if (b.title.toUpperCase() === color.toUpperCase()) {
                b.style.border = '2.5px solid #26687b';
                b.style.transform = 'scale(1.15)';
            } else {
                b.style.border = '1px solid #cbd5e1';
                b.style.transform = 'scale(1)';
            }
        });
    });

    """
    
    def repl_9(match):
        return palette_js + match.group(1)
        
    content, count = re.subn(pattern_9, repl_9, content)
    if count == 0:
        print("Error: Pattern 9 (Credenciales comment) not matched.")
        return False
    print("Edit 9 (Palette JS logic injection) applied.")

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Docentes view updated successfully!")
    return True

def update_horarios_view():
    path = r"D:\Proyectos\FrontICE\LARAVELBTI\resources\views\horarios\index.blade.php"
    if not os.path.exists(path):
        print(f"Error: Horarios view path not found: {path}")
        return False
        
    print(f"Updating horarios view: {path}...")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Find the target function renderClassCardInCell
    target_func = """    function renderClassCardInCell(cellElement, data) {
        let html = '<div class="class-card" draggable="true">';
        data.clases.forEach((clase, idx) => {
            if (idx > 0) {
                html += '<hr style="margin: 4px 0; opacity: 0.15; border-color: rgb(38, 104, 123);">';
            }
            const teacherName = clase.docente_nombre || data.docente_nombre || '';
            const aula = clase.aula || data.aula || '';
            const aulaBadge = aula ? ` <span style="font-size: 0.65rem; background-color: #f1f5f9; color: #475569; padding: 2px 4px; border-radius: 4px; border: 1px solid #e2e8f0; font-weight: 600; margin-left: 4px; display: inline-flex; align-items: center; gap: 2px;"><i class="fa-solid fa-door-open" style="font-size: 0.58rem;"></i> ${aula}</span>` : '';
            html += `
                <div class="class-subject" style="font-size: 0.85rem; font-weight: 700; line-height: 1.2; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 4px;">
                    <span>${clase.materia_nombre}</span>
                    ${aulaBadge}
                </div>
                <div class="class-detail" style="font-size: 0.72rem; color: #475569; line-height: 1.2; margin-top: 2px;"><i class="fa-solid fa-user-tie"></i> ${teacherName}</div>
            `;
        });
        html += '</div>';
        cellElement.innerHTML = html;
    }"""

    replacement_func = """    function darkenColor(hex, percent) {
        if (!hex || hex === '#FFFFFF') return '#cbd5e1';
        hex = hex.replace(/^\s*#|\s*$/g, '');
        if (hex.length === 3) {
            hex = hex.replace(/(.)/g, '$1$1');
        }
        let r = parseInt(hex.substr(0, 2), 16),
            g = parseInt(hex.substr(2, 2), 16),
            b = parseInt(hex.substr(4, 2), 16);

        r = Math.max(0, Math.min(255, r - (r * (percent / 100))));
        g = Math.max(0, Math.min(255, g - (g * (percent / 100))));
        b = Math.max(0, Math.min(255, b - (b * (percent / 100))));

        return '#' + 
            ('0' + Math.round(r).toString(16)).slice(-2) + 
            ('0' + Math.round(g).toString(16)).slice(-2) + 
            ('0' + Math.round(b).toString(16)).slice(-2);
    }

    function renderClassCardInCell(cellElement, data) {
        const firstClaseColor = (data.clases[0] && data.clases[0].docente_color) || data.docente_color || '';
        
        let cardStyle = '';
        if (firstClaseColor && firstClaseColor !== '#FFFFFF') {
            const darkBorder = darkenColor(firstClaseColor, 12);
            const leftBorder = darkenColor(firstClaseColor, 35);
            cardStyle = `style="background-color: ${firstClaseColor} !important; border-color: ${darkBorder} !important; border-left-color: ${leftBorder} !important;"`;
        }
        
        let html = `<div class="class-card" draggable="true" ${cardStyle}>`;
        data.clases.forEach((clase, idx) => {
            if (idx > 0) {
                html += '<hr style="margin: 4px 0; opacity: 0.15; border-color: rgb(38, 104, 123);">';
            }
            const teacherName = clase.docente_nombre || data.docente_nombre || '';
            const aula = clase.aula || data.aula || '';
            const aulaBadge = aula ? ` <span style="font-size: 0.65rem; background-color: #f1f5f9; color: #475569; padding: 2px 4px; border-radius: 4px; border: 1px solid #e2e8f0; font-weight: 600; margin-left: 4px; display: inline-flex; align-items: center; gap: 2px;"><i class="fa-solid fa-door-open" style="font-size: 0.58rem;"></i> ${aula}</span>` : '';
            
            // If the card has a custom color, force readable dark colors for text
            const subjectStyle = firstClaseColor && firstClaseColor !== '#FFFFFF' ? 'style="font-size: 0.85rem; font-weight: 700; line-height: 1.2; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 4px; color: #0f172a !important;"' : 'style="font-size: 0.85rem; font-weight: 700; line-height: 1.2; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 4px;"';
            const detailStyle = firstClaseColor && firstClaseColor !== '#FFFFFF' ? 'style="font-size: 0.72rem; color: #334155 !important; line-height: 1.2; margin-top: 2px;"' : 'style="font-size: 0.72rem; color: #475569; line-height: 1.2; margin-top: 2px;"';
            const iconStyle = firstClaseColor && firstClaseColor !== '#FFFFFF' ? 'style="color: #475569 !important;"' : '';
            
            html += `
                <div class="class-subject" ${subjectStyle}>
                    <span>${clase.materia_nombre}</span>
                    ${aulaBadge}
                </div>
                <div class="class-detail" ${detailStyle}><i class="fa-solid fa-user-tie" ${iconStyle}></i> ${teacherName}</div>
            `;
        });
        html += '</div>';
        cellElement.innerHTML = html;
    }"""

    if target_func not in content:
        # Check if whitespace differences are preventing exact match
        # Normalize whitespace and check
        print("Error: Target renderClassCardInCell function not found in view.")
        return False
        
    new_content = content.replace(target_func, replacement_func)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("Horarios view updated successfully!")
    return True

if __name__ == '__main__':
    ok_controller = update_controller()
    ok_docentes = update_docentes_view()
    ok_horarios = update_horarios_view()
    
    if ok_controller and ok_docentes and ok_horarios:
        print("\nAll frontend modifications applied successfully!")
        sys.exit(0)
    else:
        print("\nSome modifications failed to apply.")
        sys.exit(1)
