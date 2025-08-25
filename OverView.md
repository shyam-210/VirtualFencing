
---

# 🚨 **AI-Powered Virtual Fencing & Intrusion Detection System**

### **Core Idea**

A **low-cost, AI-based alternative** to physical fencing and expensive surveillance. The system uses cameras + YOLOv8 + OpenCV to detect intrusions across **virtual boundaries** drawn by the user.

---

## 🔹 **Main Features**

### 1. **Virtual Fence Setup**

* Users can draw **custom boundaries** on each camera feed.
* Works for **multiple cameras** simultaneously.
* Adjustable shapes (lines, polygons) for flexible coverage.

---

### 2. **Real-Time Intrusion Detection**

* YOLOv8 detects **humans, vehicles, or animals** crossing the fence.
* Direction-based detection (entry or exit).
* Works with **webcams, CCTV, or IP cameras**.

---

### 3. **Alerts & Notifications**

* Instant alert when intrusion happens:

  * **Website Dashboard notification**
  * **WhatsApp / SMS alerts** with snapshot attached
  * **Optional siren or buzzer trigger** for critical zones

---

### 4. **Snapshots & Storage**

* Automatic snapshot of intrusion taken.
* Images stored in **compressed WebP/JPEG format** (lightweight, minimal loss).
* Option to **enhance original image quality on demand**.

---

### 5. **Dashboard (Control Center)**

**Live Camera Feeds**

* Grid view of all cameras.
* Click-to-zoom single camera view.

**Alerts Panel**

* Real-time pop-up when intrusion occurs.
* Shows timestamp, camera ID, and detected object type.

**Snapshot Gallery**

* Timeline of all captured intrusions.
* Searchable & filterable by **date, camera, object type**.

**Logs Section**

* Intrusion logs stored in **CSV/SQLite**.
* Fields: Timestamp, Camera ID, Object type, Direction, Snapshot link.

**Settings Panel**

* Virtual fence customization.
* Notification preferences (SMS, WhatsApp, dashboard only).
* Storage preferences (compression, retention period).

---

## 🔹 **Additional Enhancements**

* **Lightweight & scalable** (can run on local system or Raspberry Pi).
* **Searchable Logs**: filter intrusions by date/camera/object type.
* **Future Scope**: cloud storage integration, face recognition, access control.

---

👉 In short:
This project = **Smart surveillance system** with **multi-camera live monitoring, instant intrusion alerts, searchable logs, compressed storage, and a powerful dashboard.**

---
