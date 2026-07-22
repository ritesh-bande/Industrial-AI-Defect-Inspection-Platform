import { apiGet, apiPatch, apiPost } from "./api";

function appendMetadata(formData, metadata = {}) {
  Object.entries(metadata).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      formData.append(key, value);
    }
  });
  return formData;
}

function imageFormData(file, metadata) {
  const formData = new FormData();
  formData.append("file", file);
  return appendMetadata(formData, metadata);
}

function batchFormData(files, metadata) {
  const formData = new FormData();
  Array.from(files).forEach((file) => {
    formData.append("files", file);
  });
  return appendMetadata(formData, metadata);
}

// Upload Image
export function uploadInspection(file, metadata = {}) {
  return apiPost("/api/inspections/upload", imageFormData(file, metadata));
}

// AI Inspect
export function inspectImage(file, metadata = {}) {
  return apiPost("/api/inspections/inspect", imageFormData(file, metadata));
}

// Batch Inspect
export function inspectBatch(files, metadata = {}) {
  return apiPost("/api/inspections/batch-inspect", batchFormData(files, metadata));
}

// List Inspections
export function listInspections({
  skip = 0,
  limit = 50,
  productId = "",
  productionLine = "",
  reviewStatus = "",
} = {}) {
  const params = new URLSearchParams({
    skip: String(skip),
    limit: String(limit),
  });

  if (productId) params.set("product_id", productId);
  if (productionLine) params.set("production_line", productionLine);
  if (reviewStatus) params.set("review_status", reviewStatus);

  return apiGet(`/api/inspections?${params.toString()}`);
}

// Single Inspection
export function getInspection(id) {
  return apiGet(`/api/inspections/${id}`);
}

// Update Review Status
export function updateReviewStatus(id, reviewStatus, reviewNotes = "") {
  return apiPatch(`/api/inspections/${id}/review-status`, {
    review_status: reviewStatus,
    review_notes: reviewNotes,
  });
}

// Update Metadata
export function updateInspectionMetadata(id, metadata = {}) {
  return apiPatch(`/api/inspections/${id}/metadata`, metadata);
}

// Camera Samples
export function getCameraSamples() {
  return apiGet("/api/inspections/camera-samples");
}

// Camera Simulation
export function simulateCameraInspection({
  frameIndex = 0,
  label = "",
} = {}) {
  const params = new URLSearchParams({
    frame_index: String(frameIndex),
  });

  if (label) params.set("label", label);

  return apiPost(
    `/api/inspections/camera-simulate?${params.toString()}`,
    {}
  );
}