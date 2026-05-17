import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

export const uploadFace = async (file) => {
  const formData = new FormData();
  formData.append("image", file);
  const response = await api.post("/face-check", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

export const uploadVoice = async (file) => {
  const formData = new FormData();
  formData.append("audio", file);
  const response = await api.post("/voice-check", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

export const fetchRiskScore = async () => {
  const response = await api.get("/risk-score");
  return response.data;
};
