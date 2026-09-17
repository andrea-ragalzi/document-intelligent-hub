export function requiresInvitationForRegistration(): boolean {
  return (
    process.env.NODE_ENV === "production" ||
    process.env.NEXT_PUBLIC_REQUIRE_INVITATION_FOR_REGISTRATION === "true"
  );
}
