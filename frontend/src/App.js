// ==============================================================================
// src/App.js
// ==============================================================================
import './App.css';
import React, { useState, useEffect } from 'react';
import axios from 'axios';



// Configura la URL base de tu API de Django (ahora con ngrok)
const API_URL = 'https://apigc.ayltispa.com/api';
const ADMIN_URL = 'https://apigc.ayltispa.com/admin'; // URL para el panel de admin

const apiClient = axios.create({
    baseURL: API_URL,
});

function App() {
    // --- ESTADOS DEL COMPONENTE ---
    const [propietarios, setPropietarios] = useState([]);
    const [nuevoPropietario, setNuevoPropietario] = useState({ numero_casa: '', nombre: '', apellido: '', correo_electronico: '' });
    
    // --- INICIO DE CAMBIOS: Estados para filtro y selección ---
    const [filtro, setFiltro] = useState('');
    const [seleccionados, setSeleccionados] = useState(new Set());
    // --- FIN DE CAMBIOS ---
    
    const [asunto, setAsunto] = useState(() => {
        const fecha = new Date();
        fecha.setMonth(fecha.getMonth() - 1); // Restar un mes
        const mesAnterior = fecha.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' }).toUpperCase();
        return 'GASTO COMUN ' + mesAnterior;
    });
    const [mensaje, setMensaje] = useState('');
    const [archivosComunes, setArchivosComunes] = useState([]);
    const [archivosIndividuales, setArchivosIndividuales] = useState([]);
    
    const [log, setLog] = useState([]);
    const [enviando, setEnviando] = useState(false);

    // --- LÓGICA DE GESTIÓN DE PROPIETARIOS (CONECTADA AL BACKEND) ---
    
    const fetchPropietarios = async () => {
        try {
            const response = await apiClient.get('/propietarios/', {
                headers: {
                    
                }
            });

            if (Array.isArray(response.data)) {
                setPropietarios(response.data);
            } else {
                console.error("La respuesta de la API no es un arreglo:", response.data);
                alert("Error: La respuesta del servidor no tiene el formato esperado.");
                setPropietarios([]);
            }
        } catch (error) {
            console.error("Error al cargar propietarios:", error);
            alert("No se pudo conectar con el servidor para cargar los propietarios.");
            setPropietarios([]);
        }
    };

    useEffect(() => {
        fetchPropietarios();
    }, []);

    const handlePropietarioChange = (e) => {
        const { name, value } = e.target;
        setNuevoPropietario(prev => ({ ...prev, [name]: value }));
    };

    const handleAddPropietario = async (e) => {
        e.preventDefault();
        try {
            await apiClient.post('/propietarios/', nuevoPropietario);
            fetchPropietarios();
            setNuevoPropietario({ numero_casa: '', nombre: '', apellido: '', correo_electronico: '' });
        } catch (error) {
            console.error("Error al agregar propietario:", error);
            alert(`Error al agregar propietario: ${error.response?.data?.numero_casa || 'Verifique los datos.'}`);
        }
    };

    const handleDeletePropietario = async (numero_casa) => {
        if (window.confirm(`¿Estás seguro de que quieres eliminar al propietario de la casa ${numero_casa}?`)) {
            try {
                await apiClient.delete(`/propietarios/${numero_casa}/`);
                fetchPropietarios();
            } catch (error) {
                console.error("Error al eliminar propietario:", error);
                alert("Error al eliminar propietario.");
            }
        }
    };

    // --- INICIO DE CAMBIOS: Lógica para filtro y selección ---
    const handleSelectPropietario = (numero_casa) => {
        const newSeleccionados = new Set(seleccionados);
        if (newSeleccionados.has(numero_casa)) {
            newSeleccionados.delete(numero_casa);
        } else {
            newSeleccionados.add(numero_casa);
        }
        setSeleccionados(newSeleccionados);
    };

    const filteredPropietarios = propietarios.filter(p =>
        p.numero_casa.toString().includes(filtro) ||
        p.nombre.toLowerCase().includes(filtro.toLowerCase()) ||
        p.apellido.toLowerCase().includes(filtro.toLowerCase())
    );

    const handleSelectAll = (e) => {
        if (e.target.checked) {
            const allIds = new Set(filteredPropietarios.map(p => p.numero_casa));
            setSeleccionados(allIds);
        } else {
            setSeleccionados(new Set());
        }
    };
    // --- FIN DE CAMBIOS ---

    // --- LÓGICA DE ENVÍO DE CORREOS (CONECTADA AL BACKEND) ---

    const handleEnviar = async () => {
        // --- INICIO DE CAMBIOS: Validar que haya seleccionados ---
        if (seleccionados.size === 0) {
            alert('Debe seleccionar al menos un propietario para enviar correos.');
            return;
        }
        // --- FIN DE CAMBIOS ---

        setEnviando(true);
        setLog([]);

        const formData = new FormData();
        formData.append('asunto', asunto);
        formData.append('mensaje', mensaje);
        
        for (const file of archivosComunes) {
            formData.append('archivos_comunes', file);
        }
        for (const file of archivosIndividuales) {
            formData.append('archivos_individuales', file);
        }

        // --- INICIO DE CAMBIOS: Enviar IDs seleccionados ---
        for (const casaId of seleccionados) {
            formData.append('casas_seleccionadas', casaId);
        }
        // --- FIN DE CAMBIOS ---

        try {
            const response = await apiClient.post('/enviar-gastos/', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setLog(response.data.log);
        } catch (error) {
            console.error('Error en el proceso de envío:', error);
            setLog(prev => [...prev, { tipo: 'error', casa: 'General', mensaje: `Error de conexión: ${error.message}` }]);
        } finally {
            setEnviando(false);
        }
    };

    const LogItem = ({ item }) => {
        let colorClass = 'text-gray-400';
        if (item.tipo === 'success') colorClass = 'text-green-400';
        if (item.tipo === 'error') colorClass = 'text-red-400';
        return <p className={colorClass}>{item.mensaje}</p>;
    };

    return (
        <div className="bg-gray-100 text-gray-800">
            <div className="container mx-auto p-4 md:p-8 max-w-4xl">
                <h1 className="text-3xl font-bold text-center text-gray-700 mb-8">Panel de Envío de Gastos Comunes</h1>

                {/* SECCIÓN 1: GESTIÓN DE PROPIETARIOS */}
                <div className="bg-white p-6 rounded-lg shadow-md mb-8">
                    <div className="flex justify-between items-center mb-4 border-b pb-2">
                        <h2 className="text-2xl font-semibold">1. Base de Propietarios</h2>
                        <a 
                            href={ADMIN_URL} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="bg-green-700 text-white font-bold text-sm py-1 px-3 rounded-md hover:bg-gray-700 transition-colors"
                        >
                            Admnistrar Propietarios
                        </a>
                    </div>
                    <form onSubmit={handleAddPropietario} className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                        <input type="number" name="numero_casa" value={nuevoPropietario.numero_casa} onChange={handlePropietarioChange} placeholder="N° de Casa" className="p-2 border rounded-md" required />
                        <input type="text" name="nombre" value={nuevoPropietario.nombre} onChange={handlePropietarioChange} placeholder="Nombre" className="p-2 border rounded-md" required />
                        <input type="text" name="apellido" value={nuevoPropietario.apellido} onChange={handlePropietarioChange} placeholder="Apellido" className="p-2 border rounded-md" required />
                        <input type="text" name="correo_electronico" value={nuevoPropietario.correo_electronico} onChange={handlePropietarioChange} placeholder="ej: correo1@mail.com, correo2@mail.com" className="p-2 border rounded-md" required />
                        <button type="submit" className="md:col-span-2 bg-blue-600 text-white font-bold py-2 px-4 rounded-md hover:bg-blue-700 transition-colors">Agregar Propietario</button>
                    </form>
                    
                    {/* --- INICIO DE CAMBIOS: Filtro de búsqueda --- */}
                    <div className="mb-4">
                        <input
                            type="text"
                            placeholder="Filtrar por n° de casa, nombre o apellido..."
                            className="p-2 border rounded-md w-full"
                            value={filtro}
                            onChange={e => setFiltro(e.target.value)}
                        />
                    </div>
                    {/* --- FIN DE CAMBIOS --- */}

                    <div className="overflow-x-auto">
                        <table className="min-w-full bg-white border">
                            <thead className="bg-gray-200">
                                <tr>
                                    {/* --- INICIO DE CAMBIOS: Checkbox para seleccionar todos --- */}
                                    <th className="py-2 px-2 border-b">
                                        <input
                                            type="checkbox"
                                            onChange={handleSelectAll}
                                            checked={filteredPropietarios.length > 0 && seleccionados.size === filteredPropietarios.length}
                                            disabled={filteredPropietarios.length === 0}
                                        />
                                    </th>
                                    {/* --- FIN DE CAMBIOS --- */}
                                    <th className="py-2 px-4 border-b">N° Casa</th>
                                    <th className="py-2 px-4 border-b">Nombre Completo</th>
                                    <th className="py-2 px-4 border-b">Correo(s)</th>
                                    <th className="py-2 px-4 border-b">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredPropietarios.length > 0 ? filteredPropietarios.map(p => (
                                    <tr key={p.numero_casa}>
                                        {/* --- INICIO DE CAMBIOS: Checkbox para selección individual --- */}
                                        <td className="py-2 px-2 border-b text-center">
                                            <input
                                                type="checkbox"
                                                checked={seleccionados.has(p.numero_casa)}
                                                onChange={() => handleSelectPropietario(p.numero_casa)}
                                            />
                                        </td>
                                        {/* --- FIN DE CAMBIOS --- */}
                                        <td className="py-2 px-4 border-b">{p.numero_casa}</td>
                                        <td className="py-2 px-4 border-b">{p.nombre} {p.apellido}</td>
                                        <td className="py-2 px-4 border-b">{p.correo_electronico}</td>
                                        <td className="py-2 px-4 border-b text-center">
                                            <button onClick={() => handleDeletePropietario(p.numero_casa)} className="btn-eliminar bg-red-500 text-white px-3 py-1 rounded-md text-sm hover:bg-red-600">Eliminar</button>
                                        </td>
                                    </tr>
                                )) : (
                                    <tr><td colSpan="5" className="text-center py-4">No se encontraron propietarios.</td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* SECCIÓN 2: PANEL DE ENVÍO */}
                <div className="bg-white p-6 rounded-lg shadow-md">
                    <h2 className="text-2xl font-semibold mb-4 border-b pb-2">2. Preparar y Enviar Correos ({seleccionados.size} seleccionados)</h2>
                    <div className="space-y-4">
                        <input type="text" value={asunto} onChange={e => setAsunto(e.target.value)} placeholder="Asunto del correo" className="w-full p-2 border rounded-md" />
                        <textarea rows="8" value={mensaje} onChange={e => setMensaje(e.target.value)} placeholder="Escribe aquí el mensaje común para todos los propietarios..." className="w-full p-2 border rounded-md" />
                        <div>
                            <label className="block font-medium mb-1">Adjuntos Comunes (para todos):</label>
                            <input type="file" multiple onChange={e => setArchivosComunes(Array.from(e.target.files))} className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
                        </div>
                        <div>
                            <label className="block font-medium mb-1">Carpeta con Gastos Individuales:</label>
                            <p className="text-sm text-gray-600 mb-2">Selecciona los archivos individuales. Deben llamarse como el número de casa (ej. <strong>101.pdf</strong>, <strong>102.pdf</strong>).</p>
                            <input type="file" multiple onChange={e => setArchivosIndividuales(Array.from(e.target.files))} className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100" />
                        </div>
                        <button onClick={handleEnviar} disabled={enviando || seleccionados.size === 0} className="w-full bg-green-600 text-white font-bold py-3 px-4 rounded-md hover:bg-green-700 transition-colors text-lg disabled:bg-gray-400">
                            {enviando ? 'Enviando...' : `Iniciar Envío a ${seleccionados.size} Propietarios`}
                        </button>
                    </div>
                </div>

                {/* SECCIÓN 3: LOG DE ENVÍO */}
                <div className="bg-white p-6 rounded-lg shadow-md mt-8">
                    <h2 className="text-2xl font-semibold mb-4 border-b pb-2">3. Log de Envío</h2>
                    <div className="bg-gray-900 text-white p-4 rounded-md h-64 overflow-y-auto text-sm font-mono">
                        {log.length > 0 ? log.map((item, index) => <LogItem key={index} item={item} />) : <p>Esperando inicio del proceso...</p>}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default App;