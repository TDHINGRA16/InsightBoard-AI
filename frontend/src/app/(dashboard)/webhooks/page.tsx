"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api } from "@/lib/api";
import { PageHeader, EmptyState, Loading } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    Webhook as WebhookIcon,
    Plus,
    Trash2,
    Play,
    CheckCircle,
    XCircle,
} from "lucide-react";
import { Webhook, WebhookEventType } from "@/types";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";

const webhookSchema = z.object({
    event_type: z.string().min(1, "Event type is required"),
    endpoint_url: z.string().url("Must be a valid URL"),
    description: z.string().optional(),
});

type WebhookFormData = z.infer<typeof webhookSchema>;

export default function WebhooksPage() {
    const queryClient = useQueryClient();
    const [dialogOpen, setDialogOpen] = useState(false);

    const { data, isLoading } = useQuery({
        queryKey: ["webhooks"],
        queryFn: async () => {
            const response = await api.getWebhooks();
            return response.data;
        },
    });

    const createWebhookMutation = useMutation({
        mutationFn: async (data: WebhookFormData) => {
            const response = await api.createWebhook(data);
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["webhooks"] });
            setDialogOpen(false);
            toast.success("Webhook created");
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Failed to create webhook");
        },
    });

    const deleteWebhookMutation = useMutation({
        mutationFn: async (id: string) => {
            await api.deleteWebhook(id);
            return id;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["webhooks"] });
            toast.success("Webhook deleted");
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Failed to delete webhook");
        },
    });

    const testWebhookMutation = useMutation({
        mutationFn: async (id: string) => {
            const response = await api.testWebhook(id);
            return response.data;
        },
        onSuccess: () => {
            toast.success("Test event sent successfully!");
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Test failed");
        },
    });

    const form = useForm<WebhookFormData>({
        resolver: zodResolver(webhookSchema),
        defaultValues: {
            event_type: "",
            endpoint_url: "",
            description: "",
        },
    });

    const onSubmit = (data: WebhookFormData) => {
        createWebhookMutation.mutate(data);
    };

    const webhooks: Webhook[] = data?.data || [];

    if (isLoading) {
        return <Loading text="Loading webhooks..." />;
    }

    return (
        <div>
            <PageHeader
                title="Webhooks"
                description="Manage webhook subscriptions for real-time notifications"
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Webhooks" },
                ]}
                actions={
                    <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                        <DialogTrigger asChild>
                            <Button>
                                <Plus className="h-4 w-4 mr-2" />
                                Add Webhook
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>Create Webhook</DialogTitle>
                            </DialogHeader>
                            <Form {...form}>
                                <form
                                    onSubmit={form.handleSubmit(onSubmit)}
                                    className="space-y-4"
                                >
                                    <FormField
                                        control={form.control}
                                        name="event_type"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>Event Type</FormLabel>
                                                <Select
                                                    onValueChange={field.onChange}
                                                    defaultValue={field.value}
                                                >
                                                    <FormControl>
                                                        <SelectTrigger>
                                                            <SelectValue placeholder="Select event..." />
                                                        </SelectTrigger>
                                                    </FormControl>
                                                    <SelectContent>
                                                        <SelectItem value={WebhookEventType.ANALYSIS_COMPLETED}>
                                                            Analysis Completed
                                                        </SelectItem>
                                                        <SelectItem value={WebhookEventType.ANALYSIS_FAILED}>
                                                            Analysis Failed
                                                        </SelectItem>
                                                        <SelectItem value={WebhookEventType.TASK_CREATED}>
                                                            Task Created
                                                        </SelectItem>
                                                        <SelectItem value={WebhookEventType.TASK_UPDATED}>
                                                            Task Updated
                                                        </SelectItem>
                                                        <SelectItem value={WebhookEventType.TASK_COMPLETED}>
                                                            Task Completed
                                                        </SelectItem>
                                                        <SelectItem value={WebhookEventType.EXPORT_COMPLETED}>
                                                            Export Completed
                                                        </SelectItem>
                                                    </SelectContent>
                                                </Select>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />

                                    <FormField
                                        control={form.control}
                                        name="endpoint_url"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>Endpoint URL</FormLabel>
                                                <FormControl>
                                                    <Input
                                                        placeholder="https://your-server.com/webhook"
                                                        {...field}
                                                    />
                                                </FormControl>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />

                                    <FormField
                                        control={form.control}
                                        name="description"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>Description (optional)</FormLabel>
                                                <FormControl>
                                                    <Input
                                                        placeholder="My webhook for..."
                                                        {...field}
                                                    />
                                                </FormControl>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />

                                    <Button
                                        type="submit"
                                        className="w-full"
                                        disabled={createWebhookMutation.isPending}
                                    >
                                        {createWebhookMutation.isPending
                                            ? "Creating..."
                                            : "Create Webhook"}
                                    </Button>
                                </form>
                            </Form>
                        </DialogContent>
                    </Dialog>
                }
            />

            {webhooks.length === 0 ? (
                <EmptyState
                    icon={<WebhookIcon className="h-8 w-8 text-muted-foreground" />}
                    title="No webhooks configured"
                    description="Create a webhook to receive real-time notifications about events."
                    actionLabel="Add Webhook"
                    onAction={() => setDialogOpen(true)}
                />
            ) : (
                <div className="grid gap-4 md:grid-cols-2">
                    {webhooks.map((webhook) => (
                        <WebhookCard
                            key={webhook.id}
                            webhook={webhook}
                            onDelete={(id) => deleteWebhookMutation.mutate(id)}
                            onTest={(id) => testWebhookMutation.mutate(id)}
                            isDeleting={deleteWebhookMutation.isPending}
                            isTesting={testWebhookMutation.isPending}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}

function WebhookCard({
    webhook,
    onDelete,
    onTest,
    isDeleting,
    isTesting,
}: {
    webhook: Webhook;
    onDelete: (id: string) => void;
    onTest: (id: string) => void;
    isDeleting: boolean;
    isTesting: boolean;
}) {
    return (
        <Card>
            <CardHeader className="flex flex-row items-start justify-between pb-2">
                <div>
                    <Badge variant={webhook.is_active ? "default" : "secondary"}>
                        {webhook.event_type.replace(".", " → ")}
                    </Badge>
                    {!webhook.is_active && (
                        <Badge variant="outline" className="ml-2">
                            Inactive
                        </Badge>
                    )}
                </div>
                <div className="flex items-center gap-1">
                    {webhook.is_active ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                        <XCircle className="h-4 w-4 text-red-500" />
                    )}
                </div>
            </CardHeader>
            <CardContent>
                <p className="text-sm text-muted-foreground truncate mb-2">
                    {webhook.endpoint_url}
                </p>
                {webhook.description && (
                    <p className="text-sm mb-2">{webhook.description}</p>
                )}
                {webhook.last_triggered_at && (
                    <p className="text-xs text-muted-foreground mb-3">
                        Last triggered{" "}
                        {formatDistanceToNow(new Date(webhook.last_triggered_at), {
                            addSuffix: true,
                        })}
                    </p>
                )}
                {webhook.failed_attempts > 0 && (
                    <p className="text-xs text-destructive mb-3">
                        {webhook.failed_attempts} failed attempts
                    </p>
                )}
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onTest(webhook.id)}
                        disabled={isTesting}
                    >
                        <Play className="h-3 w-3 mr-1" />
                        Test
                    </Button>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDelete(webhook.id)}
                        disabled={isDeleting}
                        className="text-destructive hover:text-destructive"
                    >
                        <Trash2 className="h-3 w-3 mr-1" />
                        Delete
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}
