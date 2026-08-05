import { apiGet, apiPatch, apiPost } from "./api";

export function listReworkTickets(status = "") {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  const query = params.toString();
  return apiGet(`/api/rework/tickets${query ? `?${query}` : ""}`);
}

export function createReworkTicket(payload) {
  return apiPost("/api/rework/tickets", payload);
}

export function getReworkTicketByInspection(inspectionId) {
  return apiGet(`/api/rework/tickets/by-inspection/${inspectionId}`);
}

export function updateReworkTicket(ticketId, payload) {
  return apiPatch(`/api/rework/tickets/${ticketId}`, payload);
}
