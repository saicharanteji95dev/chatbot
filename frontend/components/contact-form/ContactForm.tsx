"use client";

import { useState } from "react";
import { supabase } from "@/lib/supabase";

export default function ContactForm({ question }: { question: string }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async () => {
    if (!name || !email) {
      alert("Name and Email are required");
      return;
    }

    const { error } = await supabase.from("contact_leads").insert({
      name,
      email,
      phone,
      question,
    });

    if (!error) setSubmitted(true);
  };

  if (submitted) {
    return (
      <div className="border-t bg-green-50 p-4">
        ✅ Thank you! i95Dev will contact you shortly.
      </div>
    );
  }

  return (
    <div className="border-t bg-muted p-4">
      <h3 className="font-semibold mb-2">
        Contact i95Dev for more information
      </h3>

      <div className="flex gap-2 flex-wrap">
        <input
          className="border p-2 flex-1"
          placeholder="Name"
          onChange={(e) => setName(e.target.value)}
        />
        <input
          className="border p-2 flex-1"
          placeholder="Email"
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          className="border p-2 flex-1"
          placeholder="Phone"
          onChange={(e) => setPhone(e.target.value)}
        />

        <button
          className="bg-primary text-white px-4"
          onClick={handleSubmit}
        >
          Submit
        </button>
      </div>
    </div>
  );
}
