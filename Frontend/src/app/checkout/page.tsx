"use client";

import * as React from "react";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowLeft,
  CreditCard,
  Lock,
  CheckCircle,
  ShoppingCart,
  Wallet,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useProduct } from "@/hooks/useApi";
import { formatCurrency } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { useWallet, useConnection } from "@solana/wallet-adapter-react";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";
import {
  PublicKey,
  Transaction,
  SystemProgram,
  LAMPORTS_PER_SOL,
} from "@solana/web3.js";

type PaymentMethod = "credit-card" | "solana";

interface OrderItemProps {
  productId: string;
}

function OrderItem({ productId }: OrderItemProps) {
  const { data, isLoading } = useProduct(productId);
  const product = data?.product;

  if (isLoading) {
    return (
      <div className="flex gap-3 py-3">
        <Skeleton className="h-16 w-16 rounded-md" />
        <div className="flex-1 space-y-1">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-16" />
        </div>
      </div>
    );
  }

  if (!product) return null;

  return (
    <div className="flex gap-3 py-3">
      <div className="relative h-16 w-16 flex-shrink-0 overflow-hidden rounded-md bg-muted">
        {product.imageUrl ? (
          <Image
            src={product.imageUrl}
            alt={product.name}
            fill
            className="object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <ShoppingCart className="h-6 w-6 text-muted-foreground" />
          </div>
        )}
      </div>
      <div className="flex flex-1 justify-between">
        <div>
          <p className="font-medium text-sm">{product.name}</p>
          <p className="text-xs text-muted-foreground">{product.brand}</p>
        </div>
        <p className="font-semibold text-sm">{formatCurrency(product.price)}</p>
      </div>
    </div>
  );
}

// Solana payment component
function SolanaPayment({
  onSuccess,
  isProcessing,
  setIsProcessing,
}: {
  onSuccess: (signature: string) => void;
  isProcessing: boolean;
  setIsProcessing: (v: boolean) => void;
}) {
  const { publicKey, sendTransaction, connected } = useWallet();
  const { connection } = useConnection();
  const [error, setError] = React.useState<string | null>(null);
  const [txSignature, setTxSignature] = React.useState<string | null>(null);

  // Merchant wallet address - replace with your actual wallet for production
  const MERCHANT_WALLET = new PublicKey(
    "11111111111111111111111111111111" // System program address for demo - replace with actual merchant wallet
  );

  // Amount in SOL (for demo purposes, using a small amount)
  const PAYMENT_AMOUNT_SOL = 0.001;

  const handlePayment = async () => {
    if (!publicKey || !connected) {
      setError("Please connect your wallet first");
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      // Create a transaction to send SOL to the merchant
      const transaction = new Transaction().add(
        SystemProgram.transfer({
          fromPubkey: publicKey,
          toPubkey: MERCHANT_WALLET,
          lamports: PAYMENT_AMOUNT_SOL * LAMPORTS_PER_SOL,
        })
      );

      // Get the latest blockhash
      const { blockhash } = await connection.getLatestBlockhash();
      transaction.recentBlockhash = blockhash;
      transaction.feePayer = publicKey;

      // Send the transaction
      const signature = await sendTransaction(transaction, connection);

      // Wait for confirmation
      await connection.confirmTransaction(signature, "confirmed");

      setTxSignature(signature);
      onSuccess(signature);
    } catch (err) {
      console.error("Solana payment error:", err);
      setError(
        err instanceof Error ? err.message : "Payment failed. Please try again."
      );
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-center">
        <WalletMultiButton className="!bg-gradient-to-r !from-purple-600 !to-blue-600 !rounded-lg" />
      </div>

      {connected && publicKey && (
        <div className="p-4 bg-muted rounded-lg space-y-2">
          <p className="text-sm">
            <span className="text-muted-foreground">Connected Wallet:</span>
          </p>
          <p className="text-xs font-mono break-all">{publicKey.toBase58()}</p>
        </div>
      )}

      {error && (
        <div className="p-4 bg-destructive/10 text-destructive rounded-lg text-sm">
          {error}
        </div>
      )}

      {txSignature && (
        <div className="p-4 bg-green-500/10 text-green-600 rounded-lg text-sm">
          <p className="font-medium">Transaction Submitted!</p>
          <a
            href={`https://explorer.solana.com/tx/${txSignature}?cluster=devnet`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-xs underline mt-1"
          >
            View on Solana Explorer
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      )}

      <div className="text-center text-sm text-muted-foreground">
        <p>Payment Amount: {PAYMENT_AMOUNT_SOL} SOL (Devnet)</p>
        <p className="text-xs mt-1">
          Using Solana Devnet for testing. Get free devnet SOL from{" "}
          <a
            href="https://faucet.solana.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="underline text-primary"
          >
            Solana Faucet
          </a>
        </p>
      </div>

      <Button
        onClick={handlePayment}
        className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
        size="lg"
        disabled={!connected || isProcessing}
      >
        {isProcessing ? (
          <>
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent mr-2" />
            Processing Transaction...
          </>
        ) : (
          <>
            <Wallet className="mr-2 h-4 w-4" />
            Pay with Solana
          </>
        )}
      </Button>

      <p className="text-xs text-center text-muted-foreground">
        <Lock className="inline h-3 w-3 mr-1" />
        Secure blockchain transaction on Solana Devnet
      </p>
    </div>
  );
}

export default function CheckoutPage() {
  const [cartItems, setCartItems] = React.useState<string[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isProcessing, setIsProcessing] = React.useState(false);
  const [isComplete, setIsComplete] = React.useState(false);
  const [orderNumber, setOrderNumber] = React.useState("");
  const [paymentMethod, setPaymentMethod] =
    React.useState<PaymentMethod>("credit-card");
  const [txSignature, setTxSignature] = React.useState<string | null>(null);
  const [formData, setFormData] = React.useState({
    email: "",
    cardName: "",
    cardNumber: "",
    expiry: "",
    cvc: "",
    address: "",
    city: "",
    postalCode: "",
    country: "",
  });

  React.useEffect(() => {
    const cart = JSON.parse(localStorage.getItem("cart") || "[]");
    setCartItems(cart);
    setIsLoading(false);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;

    // Format card number with spaces
    if (name === "cardNumber") {
      const formatted = value
        .replace(/\s/g, "")
        .replace(/(\d{4})/g, "$1 ")
        .trim()
        .slice(0, 19);
      setFormData((prev) => ({ ...prev, [name]: formatted }));
      return;
    }

    // Format expiry date
    if (name === "expiry") {
      const cleaned = value.replace(/\D/g, "");
      let formatted = cleaned;
      if (cleaned.length >= 2) {
        formatted = cleaned.slice(0, 2) + "/" + cleaned.slice(2, 4);
      }
      setFormData((prev) => ({ ...prev, [name]: formatted }));
      return;
    }

    // Limit CVC to 4 digits
    if (name === "cvc") {
      const formatted = value.replace(/\D/g, "").slice(0, 4);
      setFormData((prev) => ({ ...prev, [name]: formatted }));
      return;
    }

    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleCreditCardSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsProcessing(true);

    // Simulate payment processing
    await new Promise((resolve) => setTimeout(resolve, 2000));

    completeOrder();
  };

  const handleSolanaSuccess = (signature: string) => {
    setTxSignature(signature);
    completeOrder();
  };

  const completeOrder = () => {
    // Clear cart after successful payment
    localStorage.setItem("cart", JSON.stringify([]));
    window.dispatchEvent(new Event("cartUpdated"));

    setOrderNumber(`FIN-${Date.now().toString(36).toUpperCase()}`);
    setIsProcessing(false);
    setIsComplete(true);
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Skeleton className="h-10 w-48 mb-6" />
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-[500px]" />
          <Skeleton className="h-[300px]" />
        </div>
      </div>
    );
  }

  if (isComplete) {
    return (
      <div className="container mx-auto px-4 py-16">
        <Card className="max-w-lg mx-auto">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <CheckCircle className="h-16 w-16 text-green-500 mb-4" />
            <h2 className="text-2xl font-bold mb-2">Payment Successful!</h2>
            <p className="text-muted-foreground text-center mb-4">
              Thank you for your order.
              {paymentMethod === "credit-card" && formData.email && (
                <>
                  {" "}
                  A confirmation email has been sent to{" "}
                  <span className="font-medium">{formData.email}</span>
                </>
              )}
            </p>
            <p className="text-sm text-muted-foreground mb-2">
              Order #{orderNumber}
            </p>
            {txSignature && (
              <a
                href={`https://explorer.solana.com/tx/${txSignature}?cluster=devnet`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-sm text-primary underline mb-4"
              >
                View Transaction on Solana Explorer
                <ExternalLink className="h-4 w-4" />
              </a>
            )}
            <Link href="/search">
              <Button>Continue Shopping</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (cartItems.length === 0) {
    return (
      <div className="container mx-auto px-4 py-16">
        <Card className="max-w-lg mx-auto">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <ShoppingCart className="h-16 w-16 text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">Your cart is empty</h2>
            <p className="text-muted-foreground mb-6">
              Add some items to your cart before checking out.
            </p>
            <Link href="/search">
              <Button>Start Shopping</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center gap-4">
        <Link href="/cart">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Cart
          </Button>
        </Link>
        <h1 className="text-2xl font-bold">Checkout</h1>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Payment Form */}
        <div className="space-y-6">
          {/* Payment Method Selection */}
          <Card>
            <CardHeader>
              <CardTitle>Payment Method</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setPaymentMethod("credit-card")}
                  className={`flex flex-col items-center justify-center p-4 rounded-lg border-2 transition-colors ${
                    paymentMethod === "credit-card"
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-primary/50"
                  }`}
                >
                  <CreditCard
                    className={`h-8 w-8 mb-2 ${
                      paymentMethod === "credit-card"
                        ? "text-primary"
                        : "text-muted-foreground"
                    }`}
                  />
                  <span className="font-medium">Credit Card</span>
                  <span className="text-xs text-muted-foreground">
                    Simulated
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => setPaymentMethod("solana")}
                  className={`flex flex-col items-center justify-center p-4 rounded-lg border-2 transition-colors ${
                    paymentMethod === "solana"
                      ? "border-purple-500 bg-purple-500/5"
                      : "border-border hover:border-purple-500/50"
                  }`}
                >
                  <div
                    className={`h-8 w-8 mb-2 rounded-full flex items-center justify-center ${
                      paymentMethod === "solana"
                        ? "bg-gradient-to-r from-purple-600 to-blue-600"
                        : "bg-muted"
                    }`}
                  >
                    <span className="text-white text-lg font-bold">◎</span>
                  </div>
                  <span className="font-medium">Solana</span>
                  <span className="text-xs text-muted-foreground">
                    Blockchain
                  </span>
                </button>
              </div>
            </CardContent>
          </Card>

          {/* Credit Card Form */}
          {paymentMethod === "credit-card" && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CreditCard className="h-5 w-5" />
                  Card Details
                </CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleCreditCardSubmit} className="space-y-4">
                  <div>
                    <label className="text-sm font-medium mb-1.5 block">
                      Email Address
                    </label>
                    <Input
                      type="email"
                      name="email"
                      placeholder="you@example.com"
                      value={formData.email}
                      onChange={handleInputChange}
                      required
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-1.5 block">
                      Cardholder Name
                    </label>
                    <Input
                      type="text"
                      name="cardName"
                      placeholder="John Doe"
                      value={formData.cardName}
                      onChange={handleInputChange}
                      required
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-1.5 block">
                      Card Number
                    </label>
                    <Input
                      type="text"
                      name="cardNumber"
                      placeholder="4242 4242 4242 4242"
                      value={formData.cardNumber}
                      onChange={handleInputChange}
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium mb-1.5 block">
                        Expiry Date
                      </label>
                      <Input
                        type="text"
                        name="expiry"
                        placeholder="MM/YY"
                        value={formData.expiry}
                        onChange={handleInputChange}
                        required
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-1.5 block">
                        CVC
                      </label>
                      <Input
                        type="text"
                        name="cvc"
                        placeholder="123"
                        value={formData.cvc}
                        onChange={handleInputChange}
                        required
                      />
                    </div>
                  </div>

                  <hr className="my-4" />

                  <div>
                    <label className="text-sm font-medium mb-1.5 block">
                      Billing Address
                    </label>
                    <Input
                      type="text"
                      name="address"
                      placeholder="123 Main Street"
                      value={formData.address}
                      onChange={handleInputChange}
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium mb-1.5 block">
                        City
                      </label>
                      <Input
                        type="text"
                        name="city"
                        placeholder="New York"
                        value={formData.city}
                        onChange={handleInputChange}
                        required
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-1.5 block">
                        Postal Code
                      </label>
                      <Input
                        type="text"
                        name="postalCode"
                        placeholder="10001"
                        value={formData.postalCode}
                        onChange={handleInputChange}
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-1.5 block">
                      Country
                    </label>
                    <Input
                      type="text"
                      name="country"
                      placeholder="United States"
                      value={formData.country}
                      onChange={handleInputChange}
                      required
                    />
                  </div>

                  <Button
                    type="submit"
                    className="w-full"
                    size="lg"
                    disabled={isProcessing}
                  >
                    {isProcessing ? (
                      <>
                        <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent mr-2" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Lock className="mr-2 h-4 w-4" />
                        Pay Now
                      </>
                    )}
                  </Button>

                  <p className="text-xs text-center text-muted-foreground">
                    <Lock className="inline h-3 w-3 mr-1" />
                    This is a simulated payment. No real charges will be made.
                  </p>
                </form>
              </CardContent>
            </Card>
          )}

          {/* Solana Payment */}
          {paymentMethod === "solana" && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <div className="h-5 w-5 rounded-full bg-gradient-to-r from-purple-600 to-blue-600 flex items-center justify-center">
                    <span className="text-white text-xs font-bold">◎</span>
                  </div>
                  Pay with Solana
                </CardTitle>
              </CardHeader>
              <CardContent>
                <SolanaPayment
                  onSuccess={handleSolanaSuccess}
                  isProcessing={isProcessing}
                  setIsProcessing={setIsProcessing}
                />
              </CardContent>
            </Card>
          )}
        </div>

        {/* Order Summary */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Order Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="divide-y">
                {cartItems.map((productId) => (
                  <OrderItem key={productId} productId={productId} />
                ))}
              </div>

              <hr className="my-4" />

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Subtotal ({cartItems.length} items)</span>
                  <span className="text-muted-foreground">Calculated</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Shipping</span>
                  <span className="text-green-600">Free</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Tax</span>
                  <span className="text-muted-foreground">Calculated</span>
                </div>
                <hr className="my-2" />
                <div className="flex justify-between font-semibold text-lg">
                  <span>Total</span>
                  <span>See cart for details</span>
                </div>
              </div>

              <div className="mt-6 p-4 bg-muted rounded-lg">
                {paymentMethod === "credit-card" ? (
                  <p className="text-sm text-muted-foreground">
                    🔒 <strong>Secure Checkout</strong> — Credit card payment is
                    simulated. No real charges will be made.
                  </p>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    ◎ <strong>Blockchain Payment</strong> — Real Solana
                    transaction on Devnet. Get free test SOL from the{" "}
                    <a
                      href="https://faucet.solana.com/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline text-primary"
                    >
                      Solana Faucet
                    </a>
                    .
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
