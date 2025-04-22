### 🕒 Completed Time: Time-Based Completion Tracking per Attendee (in Hours)

This addon enhances Odoo eLearning by introducing a new metric: **Completed Time**, computed **per attendee**, which represents the **sum of the completion times (in hours)** of the slides they have completed.

#### 🔧 What's Built-In vs. What's Added

**Built-in (Odoo):**
- **Progress**
  `Progress = Number of Completed Slides / Total Number of Slides`
  → A simple ratio, based only on slide count.

**Added by this addon:**
- **Completed Time (in hours)**
  `Completed Time = Σ(completion_time of each completed slide)`
  → A cumulative total of time-based effort for each attendee.

#### 💡 Why This Matters

- ⏱️ **Duration-Aware Insight**
  Accurately reflects how much content a learner has completed, by time spent rather than steps clicked.

- 👤 **Per-Attendee Computation**
  Each attendee has a personalized Completed Time value, making metrics more meaningful for trainers and reports.

- 📊 **Actionable Training Analytics**
  Trainers can better identify high-effort learners and tailor support accordingly.

#### 🧪 Example

For a course with 10 slides (total 20 hours), if an attendee completes:

- 1 slide of 15 hours
→ **Progress**: 10%
→ **Completed Time**: 15h

---

This addon is ideal for serious training environments, compliance programs, and professional development, where **time commitment** is a better measure than simple slide count.
