export default function Home() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center bg-background px-6 text-center">
      <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
        Welcome to i95Dev
      </h1>
      <p className="mt-4 max-w-xl text-lg text-muted-foreground">
        Have a question? Click the chat icon in the bottom-right corner to talk
        with our AI assistant.
      </p>
    </main>
  );
}
