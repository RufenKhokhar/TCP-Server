import socket
import threading
import logging
import time

# Logging configuration
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

HOST = '0.0.0.0'
PORT = 65432

clients = set()
clients_lock = threading.Lock()

def broadcast(message, sender_conn):
    """Broadcast message to all clients except the sender."""
    to_remove = []
    with clients_lock:
        for client in clients:
            if client is sender_conn:
                continue
            try:
                client.sendall(message)
            except Exception as e:
                logging.warning(f"[ERROR] Failed to send to client: {e}")
                to_remove.append(client)

        for client in to_remove:
            logging.info(f"[REMOVING] Stale client removed")
            clients.discard(client)
            try:
                client.close()
            except Exception:
                pass

def handle_client(conn, addr):
    """Client communication handler."""
    logging.info(f"[NEW CONNECTION] {addr} connected.")

    # Enable TCP_NODELAY for low latency
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    with clients_lock:
        clients.add(conn)

    try:
        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    logging.info(f"[DISCONNECTED] {addr} sent empty data (connection closed).")
                    break
                message = data.decode(errors='replace').strip()
                logging.info(f"[{addr}] {message}")
                broadcast(data, conn)

    except ConnectionResetError:
        logging.warning(f"[DISCONNECTED] {addr} (Connection reset)")
    except Exception as e:
        logging.error(f"[ERROR] Exception with {addr}: {e}")
    finally:
        with clients_lock:
            if conn in clients:
                clients.remove(conn)
        try:
            conn.close()
        except Exception:
            pass
        logging.info(f"[CLOSED] Connection with {addr} closed.")
        logging.info(f"[CLIENTS REMAINING] {len(clients)}")

def start_server():
    """Start and run the TCP server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        server.settimeout(1.0)  # Allow periodic interruptions
        logging.info(f"[STARTED] Server listening on {HOST}:{PORT}")

        while True:
            try:
                conn, addr = server.accept()
                thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                thread.start()
                logging.info(f"[NEW THREAD] Started for {addr}. Active threads: {threading.active_count() - 1}")
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                logging.info("[SHUTDOWN] Keyboard interrupt received, shutting down.")
                break
            except Exception as e:
                logging.error(f"[FATAL ERROR] {e}")
                break

if __name__ == "__main__":
    start_server()
