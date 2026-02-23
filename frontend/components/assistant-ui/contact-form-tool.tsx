"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  UserIcon,
  MailIcon,
  PhoneIcon,
  BuildingIcon,
  MessageSquareIcon,
} from "lucide-react";

interface ContactFormToolProps {
  args: {
    message?: string;
    user_query?: string;
  };
}

export function ContactFormTool({ args }: ContactFormToolProps) {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    company: "",
    message: args?.message || "",
    query_context: args?.user_query || "",
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const result = await res.json();

      if (result.success) {
        setIsSubmitted(true);
      } else {
        console.error("Contact submission failed:", result.message);
      }
    } catch (err) {
      console.error("Submission error:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSubmitted) {
    return (
      <Card className="w-full max-w-md mt-4 bg-green-50 border-green-200">
        <CardContent className="pt-6 text-center">
          <div className="text-green-800 font-semibold text-lg mb-2">
            ✅ Thank you!
          </div>
          <div className="text-green-700 text-sm">
            Our integration experts will contact you shortly.
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="mt-4 space-y-4">
      {/* Info Message */}
      <div className="bg-orange-50 border border-orange-200 rounded-md p-3 text-sm text-orange-800">
        <div className="flex items-start gap-2">
          <MessageSquareIcon className="w-4 h-4 mt-0.5" />
          <div>
            {args?.message ||
              "I don't have detailed information about this topic. Please connect with our integration experts for personalized assistance."}
          </div>
        </div>
      </div>

      {/* Contact Form */}
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-base">
            Connect with Our Integration Expert
          </CardTitle>
          <CardDescription>
            Get personalized support for your ERP & eCommerce integration needs.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <label className="text-sm font-medium flex items-center gap-1">
                <UserIcon className="w-4 h-4" />
                Full Name *
              </label>
              <Input
                name="name"
                required
                value={formData.name}
                onChange={handleChange}
                placeholder="John Doe"
              />
            </div>

            <div>
              <label className="text-sm font-medium flex items-center gap-1">
                <MailIcon className="w-4 h-4" />
                Email *
              </label>
              <Input
                type="email"
                name="email"
                required
                value={formData.email}
                onChange={handleChange}
                placeholder="john@company.com"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-sm font-medium flex items-center gap-1">
                  <PhoneIcon className="w-4 h-4" />
                  Phone
                </label>
                <Input
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="+1 555-0000"
                />
              </div>

              <div>
                <label className="text-sm font-medium flex items-center gap-1">
                  <BuildingIcon className="w-4 h-4" />
                  Company
                </label>
                <Input
                  name="company"
                  value={formData.company}
                  onChange={handleChange}
                  placeholder="Acme Corp"
                />
              </div>
            </div>

            <div>
              <label className="text-sm font-medium">
                Describe Your Requirement *
              </label>
            </div>

            <Button type="submit" disabled={isSubmitting} className="w-full">
              {isSubmitting ? "Submitting..." : "Connect with Expert"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
