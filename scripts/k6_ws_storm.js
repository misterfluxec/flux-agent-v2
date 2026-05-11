import ws from 'k6/ws';
import { check, sleep } from 'k6';

export const options = {
    scenarios: {
        reconnect_storm: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '30s', target: 1000 }, // Ramp-up a 1000 clientes concurrentes
                { duration: '1m', target: 1000 },  // Mantener 1000 clientes (Reconnect Storm)
                { duration: '10s', target: 0 },    // Ramp-down
            ],
        },
    },
};

// Se asume que el backend WebSocket está corriendo en ws://localhost:8000
const WS_URL = 'ws://localhost:8000/api/v1/ws/realtime';

export default function () {
    const tenantId = 'tenant_stress_test';
    const userId = `user_${__VU}`;
    
    // URL simulada usando los parámetros de query
    const url = `${WS_URL}?tenant_id=${tenantId}&user_id=${userId}`;

    const res = ws.connect(url, {}, function (socket) {
        socket.on('open', function () {
            // Cliente se conectó
            // Simulamos inestabilidad de red (Reconnect storm)
            // Desconectarse después de un tiempo aleatorio entre 1s y 5s
            const sleepTime = Math.random() * 4000 + 1000;
            socket.setTimeout(function () {
                socket.close();
            }, sleepTime);
        });

        socket.on('message', function (msg) {
            // Validamos que recibimos ping o eventos
            check(msg, { 'received message': (m) => m.length > 0 });
        });

        socket.on('close', function () {
            // El cliente se cerró (emula la reconexión que K6 reintentará en la siguiente iteración del VU)
        });
        
        socket.on('error', function (e) {
            if (e.error() != "websocket: close sent") {
                console.log('Error de WebSocket: ', e.error());
            }
        });
    });

    check(res, { 'status is 101': (r) => r && r.status === 101 });
    sleep(0.5); // Breve espera antes de que el VU vuelva a intentar conectarse
}
