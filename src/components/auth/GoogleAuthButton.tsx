import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { lovable } from "@/integrations/lovable";
import { Chrome } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

interface GoogleAuthButtonProps {
  onSuccess?: () => void;
  redirectUri?: string;
  className?: string;
}

export function GoogleAuthButton({ onSuccess, redirectUri, className }: GoogleAuthButtonProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleGoogleSignIn = async () => {
    setIsLoading(true);
    try {
      const result = await lovable.auth.signInWithOAuth("google", {
        redirect_uri: redirectUri || window.location.origin,
      });

      if (result.error) {
        toast.error("Error al iniciar sesión con Google", {
          description: result.error.message,
        });
        return;
      }

      if (result.redirected) {
        // User is being redirected to Google
        return;
      }

      toast.success("¡Inicio de sesión exitoso!");
      onSuccess?.();
    } catch (error) {
      console.error("Google sign-in error:", error);
      toast.error("Error inesperado al iniciar sesión");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Button
      variant="outline"
      onClick={handleGoogleSignIn}
      disabled={isLoading}
      className={className}
    >
      <Chrome className="mr-2 h-4 w-4" />
      {isLoading ? "Conectando..." : "Continuar con Google"}
    </Button>
  );
}

export function AuthCard() {
  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-bold">Bienvenido a Q-Orchestrator</CardTitle>
        <CardDescription>
          Inicia sesión para acceder al middleware cuántico
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <GoogleAuthButton className="w-full" />
        <p className="text-xs text-center text-muted-foreground">
          Al continuar, aceptas nuestros términos de servicio y política de privacidad.
        </p>
      </CardContent>
    </Card>
  );
}
