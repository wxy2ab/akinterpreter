import ChatWindow from '@/components/ChatWindow';

export default function Home() {
  return (
    <main className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Akinterpreter</h1>
      <p className="text-lg mb-4">play with real data</p>
      <ChatWindow />
    </main>
  );
}