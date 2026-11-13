// API adresi: EXPO_PUBLIC_API_URL ortam değişkeniyle verilir (gizli bilgi değildir).
//  - Android emülatörü: http://10.0.2.2:8000
//  - Gerçek telefon (aynı Wi-Fi): http://<bilgisayarın-yerel-IP'si>:8000
//  - Üretim: https://... (mutlaka HTTPS)
export const API_URL: string = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";
