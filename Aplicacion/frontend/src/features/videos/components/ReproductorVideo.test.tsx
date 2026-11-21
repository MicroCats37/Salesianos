// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ReproductorVideo } from "./ReproductorVideo";

describe("ReproductorVideo", () => {
  it("starts the live signal automatically and muted", () => {
    render(
      <ReproductorVideo
        url="https://salesianosfest.pe/live/studio-1/index.m3u8"
        titulo="Transmisión en vivo"
        autoPlay
      />,
    );

    const player = screen.getByLabelText(
      "Transmisión en vivo",
    ) as HTMLVideoElement;

    expect(player.autoplay).toBe(true);
    expect(player.muted).toBe(true);
    expect(player.playsInline).toBe(true);
  });

  it("does not autoplay an archived video by default", () => {
    render(
      <ReproductorVideo
        url="https://salesianosfest.pe/videos/final.mp4"
        titulo="Final archivada"
      />,
    );

    const player = screen.getByLabelText("Final archivada") as HTMLVideoElement;

    expect(player.autoplay).toBe(false);
    expect(player.muted).toBe(false);
  });
});
