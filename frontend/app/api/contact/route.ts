import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    console.log("📩 Contact Form Submission:", body);

    // TODO: Save to database / Supabase / CRM
    // Example:
    // await supabase.from("contact_leads").insert(body);

    return NextResponse.json({
      success: true,
      message: "Contact request submitted successfully",
    });
  } catch (error) {
    console.error("Contact API Error:", error);

    return NextResponse.json(
      {
        success: false,
        message: "Failed to submit contact request",
      },
      { status: 500 }
    );
  }
}
